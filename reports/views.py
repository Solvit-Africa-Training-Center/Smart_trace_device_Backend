import random
from rest_framework import status, serializers, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from .models import Report
from .serializers import ReportSerializer

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
