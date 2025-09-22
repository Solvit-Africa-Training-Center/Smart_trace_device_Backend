import random
from rest_framework import status, serializers, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from .models import Report
from .serializers import ReportSerializer
from devices.models import LostItem, FoundItem
from django.db.models import Count

# ======================
# Response Serializers (for Swagger docs only)
# ======================
class ReportCreateResponseSerializer(serializers.Serializer):
	message = serializers.CharField()
	report_id = serializers.IntegerField()

class ReportListResponseSerializer(serializers.Serializer):
	results = ReportSerializer(many=True)

class ErrorResponseSerializer(serializers.Serializer):
	error = serializers.CharField()

@extend_schema(
	tags=["Reports"],
	request=ReportSerializer,
	responses={201: ReportCreateResponseSerializer, 400: ErrorResponseSerializer},
	summary="Create a report",
	description="Creates a new report for a lost or found item."
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_report(request):
	serializer = ReportSerializer(data=request.data)
	if serializer.is_valid():
		report = serializer.save(user=request.user)
		return Response({
			'message': 'Report created successfully.',
			'report_id': report.id
		}, status=status.HTTP_201_CREATED)
	return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
	tags=["Reports"],
	responses={200: ReportSerializer(many=True)},
	summary="List all reports",
	description="Lists all reports. Admin only."
)
@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def list_reports(request):
	reports = Report.objects.all().order_by('-report_date')
	serializer = ReportSerializer(reports, many=True)
	return Response(serializer.data)


@extend_schema(
    tags=["Reports"],
    responses={200: serializers.JSONField},
    summary="Location-based statistics",
    description="Aggregated statistics of lost and found items by location and top categories."
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def location_statistics(request):
    # Example heuristic: use city_town for lost and district for found when present
    lost_by_location = (
        LostItem.objects.values('city_town', 'category')
        .annotate(total=Count('id'))
        .order_by('-total')
    )
    found_by_location = (
        FoundItem.objects.values('district', 'category')
        .annotate(total=Count('id'))
        .order_by('-total')
    )

    # Build summaries: top category per location
    def summarize(rows, location_key):
        summary = {}
        for row in rows:
            loc = row.get(location_key) or 'Unknown'
            cat = row.get('category') or 'Unknown'
            total = row.get('total', 0)
            if loc not in summary:
                summary[loc] = {'total': 0, 'by_category': {}, 'top_category': None}
            summary[loc]['total'] += total
            summary[loc]['by_category'][cat] = summary[loc]['by_category'].get(cat, 0) + total
        # compute top
        for loc, data in summary.items():
            if data['by_category']:
                data['top_category'] = max(data['by_category'].items(), key=lambda kv: kv[1])[0]
        return summary

    lost_summary = summarize(lost_by_location, 'city_town')
    found_summary = summarize(found_by_location, 'district')

    return Response({
        'lost': lost_summary,
        'found': found_summary,
    })
