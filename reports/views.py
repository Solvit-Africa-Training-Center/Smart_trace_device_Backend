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
from django.db.models.functions import TruncMonth
from authentication.models import User
from devices.models import Match, Return
from datetime import datetime

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


@extend_schema(
	tags=["Reports"],
	responses={200: serializers.JSONField},
	summary="Monthly counts for key metrics",
	description=(
		"Returns monthly counts for lost items, found items, matches, returns, and new users. "
		"Accepts optional start and end in YYYY-MM; defaults to last 6 months."
	)
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def monthly_statistics(request):
	# Parse range
	start_param = request.query_params.get('start')
	end_param = request.query_params.get('end')

	def parse_ym(ym: str):
		try:
			return datetime.strptime(ym, '%Y-%m')
		except Exception:
			return None

	end_dt = parse_ym(end_param) or datetime.utcnow().replace(day=1)
	# default to 6-month window ending at end_dt
	if start_param:
		start_dt = parse_ym(start_param)
	else:
		# go back 5 months from end (inclusive makes 6 labels)
		month = end_dt.month - 5
		year = end_dt.year
		while month <= 0:
			month += 12
			year -= 1
		start_dt = datetime(year, month, 1)

	# Helper to build consecutive months list
	def month_range(start: datetime, end: datetime):
		months = []
		y, m = start.year, start.month
		while (y < end.year) or (y == end.year and m <= end.month):
			months.append((y, m))
			m += 1
			if m == 13:
				m = 1
				y += 1
		return months

	months = month_range(start_dt, end_dt)
	labels = [f"{datetime(y, m, 1):%b %Y}" for (y, m) in months]

	# Query and aggregate per month for each model
	def aggregate(model, date_field):
		qs = (
			model.objects.filter(**{f"{date_field}__date__gte": start_dt.date(), f"{date_field}__date__lte": end_dt.date()})
			.annotate(month=TruncMonth(date_field))
			.values('month')
			.annotate(total=Count('id'))
		)
		by_month = { (row['month'].year, row['month'].month): row['total'] for row in qs }
		return [by_month.get((y, m), 0) for (y, m) in months]

	lost_counts = aggregate(LostItem, 'date_reported')
	found_counts = aggregate(FoundItem, 'date_reported')
	match_counts = aggregate(Match, 'match_date')
	return_counts = aggregate(Return, 'return_date')
	user_counts = aggregate(User, 'date_joined')

	return Response({
		'labels': labels,
		'series': {
			'lost_items': lost_counts,
			'found_items': found_counts,
			'matches': match_counts,
			'returns': return_counts,
			'new_users': user_counts,
		}
	})
