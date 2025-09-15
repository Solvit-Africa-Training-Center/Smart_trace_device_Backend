from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Notification
from .serializers import NotificationSerializer

class NotificationMarkReadResponseSerializer(Response):
	message = 'Notification marked as read.'

@extend_schema(
	tags=["Notifications"],
	responses=NotificationSerializer(many=True),
	summary="List notifications",
	description="List all notifications for the authenticated user."
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_list(request):
	notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
	serializer = NotificationSerializer(notifications, many=True)
	return Response(serializer.data)

@extend_schema(
	tags=["Notifications"],
	responses={200: NotificationSerializer},
	summary="Mark notification as read",
	description="Mark a notification as read by ID."
)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def notification_mark_read(request, id):
	try:
		notification = Notification.objects.get(id=id, user=request.user)
	except Notification.DoesNotExist:
		return Response({'error': 'Notification not found.'}, status=status.HTTP_404_NOT_FOUND)
	notification.is_read = True
	notification.save()
	serializer = NotificationSerializer(notification)
	return Response(serializer.data, status=status.HTTP_200_OK)
