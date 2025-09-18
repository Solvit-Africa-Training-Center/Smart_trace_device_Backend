
from drf_spectacular.utils import extend_schema
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from django.core.mail import send_mail
from .models import Device, LostItem, FoundItem, Match, Return, Contact
from .Serializers import DeviceSerializer
from .Serializers import LostItemSerializer, FoundItemSerializer, MatchSerializer, ReturnSerializer, ContactSerializer

@extend_schema(
	tags=["Device"],
	request=DeviceSerializer, responses=DeviceSerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def device_create(request):
	serializer = DeviceSerializer(data=request.data, context={'request': request})
	if serializer.is_valid():
		serializer.save(user=request.user)
		return Response(serializer.data, status=status.HTTP_201_CREATED)
	return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
	tags=["Device"],
	responses=DeviceSerializer(many=True))
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_devices_list(request):
	devices = Device.objects.filter(user=request.user)
	serializer = DeviceSerializer(devices, many=True)
	return Response(serializer.data)

@extend_schema(
	tags=["Device"],
	responses=DeviceSerializer(many=True))
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def device_search(request):
	serial_number = request.query_params.get('serial_number')
	if serial_number:
		devices = Device.objects.filter(serial_number=serial_number)
	else:
		devices = Device.objects.none()
	serializer = DeviceSerializer(devices, many=True)
	return Response(serializer.data)

@extend_schema(
	tags=["Device"],
	responses=None)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def device_delete(request, id):
	try:
		device = Device.objects.get(id=id, user=request.user)
	except Device.DoesNotExist:
		return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
	device.delete()
	return Response(status=status.HTTP_204_NO_CONTENT)

@extend_schema(
	tags=["Device"],
    request=LostItemSerializer, responses=LostItemSerializer)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def lostitem_create(request):
	serializer = LostItemSerializer(data=request.data, context={'request': request})
	if serializer.is_valid():
		serializer.save()
		return Response(serializer.data, status=status.HTTP_201_CREATED)
	return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    tags=["Device"],
    request=LostItemSerializer, responses=LostItemSerializer)
@api_view(['PUT', 'PATCH'])
@permission_classes([permissions.AllowAny])
def lostitem_update(request, id):
    try:
        item = LostItem.objects.get(id=id)
    except LostItem.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
    partial = request.method == 'PATCH'
    serializer = LostItemSerializer(item, data=request.data, partial=partial, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    tags=["Device"],
    responses=None)
@api_view(['DELETE'])
@permission_classes([permissions.AllowAny])
def lostitem_delete(request, id):
    try:
        item = LostItem.objects.get(id=id)
    except LostItem.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
    item.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@extend_schema(
	tags=["Device"],
	responses=LostItemSerializer(many=True))
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def lostitem_list(request):
	items = LostItem.objects.all().order_by('-date_reported')
	serializer = LostItemSerializer(items, many=True)
	return Response(serializer.data)

@extend_schema(
	tags=["Device"],
	responses=LostItemSerializer(many=True))
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def lostitem_search(request):
	name = request.query_params.get('name')
	category = request.query_params.get('category')
	color = request.query_params.get('color')
	serial_number = request.query_params.get('serial_number')
	status = request.query_params.get('status', 'lost')  # Default to lost
	
	queryset = LostItem.objects.all()
	if name:
		queryset = queryset.filter(name__icontains=name)
	if category:
		queryset = queryset.filter(category__icontains=category)
	if color:
		queryset = queryset.filter(color__icontains=color)
	if serial_number:
		queryset = queryset.filter(serial_number__icontains=serial_number)
	if status:
		queryset = queryset.filter(status=status)
	
	serializer = LostItemSerializer(queryset, many=True)
	return Response(serializer.data)

@extend_schema(
	tags=["Device"],
    request=FoundItemSerializer, responses=FoundItemSerializer)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def founditem_create(request):
	serializer = FoundItemSerializer(data=request.data, context={'request': request})
	if serializer.is_valid():
		found_item = serializer.save()
		serial_number = getattr(found_item, 'serial_number', None)
		if serial_number:
			from notifications.models import Notification
			matching_lost_qs = LostItem.objects.filter(serial_number=serial_number, status='lost').order_by('-date_reported')
			for lost_item in matching_lost_qs:
				if lost_item.user:
					Notification.objects.create(
						user=lost_item.user,
						message=f"A found item matching your lost device (serial {serial_number}) was reported."
					)
				if getattr(lost_item, 'contact_email', None):
					try:
						subject = 'Possible match for your lost item'
						message = (
							f"Hello, a found item may match your lost device with serial {serial_number}. "
							f"Item name: {found_item.name}."
						)
						send_mail(subject, message, getattr(settings, 'DEFAULT_FROM_EMAIL', None), [lost_item.contact_email], fail_silently=True)
					except Exception:
						pass
		return Response(serializer.data, status=status.HTTP_201_CREATED)
	return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    tags=["Device"],
    request=FoundItemSerializer, responses=FoundItemSerializer)
@api_view(['PUT', 'PATCH'])
@permission_classes([permissions.AllowAny])
def founditem_update(request, id):
    try:
        item = FoundItem.objects.get(id=id)
    except FoundItem.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
    partial = request.method == 'PATCH'
    serializer = FoundItemSerializer(item, data=request.data, partial=partial, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    tags=["Device"],
    responses=None)
@api_view(['DELETE'])
@permission_classes([permissions.AllowAny])
def founditem_delete(request, id):
    try:
        item = FoundItem.objects.get(id=id)
    except FoundItem.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
    item.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@extend_schema(
	tags=["Device"],
	responses=FoundItemSerializer(many=True))
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def founditem_list(request):
	items = FoundItem.objects.all().order_by('-date_reported')
	serializer = FoundItemSerializer(items, many=True)
	return Response(serializer.data)

@extend_schema(
	tags=["Device"],
	responses=FoundItemSerializer(many=True))
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def founditem_search(request):
	name = request.query_params.get('name')
	category = request.query_params.get('category')
	color = request.query_params.get('color')
	serial_number = request.query_params.get('serial_number')
	status = request.query_params.get('status', 'found')  # Default to found
	
	queryset = FoundItem.objects.all()
	if name:
		queryset = queryset.filter(name__icontains=name)
	if category:
		queryset = queryset.filter(category__icontains=category)
	if color:
		queryset = queryset.filter(color__icontains=color)
	if serial_number:
		queryset = queryset.filter(serial_number__icontains=serial_number)
	if status:
		queryset = queryset.filter(status=status)
	
	serializer = FoundItemSerializer(queryset, many=True)
	return Response(serializer.data)

@extend_schema(
	tags=["Device"],
	request=MatchSerializer, responses=MatchSerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def match_create(request):
	serializer = MatchSerializer(data=request.data, context={'request': request})
	if serializer.is_valid():
		serializer.save()
		return Response(serializer.data, status=status.HTTP_201_CREATED)
	return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
	tags=["Device"],
	responses=MatchSerializer(many=True))
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def match_list(request):
	matches = Match.objects.all().order_by('-match_date')
	serializer = MatchSerializer(matches, many=True)
	return Response(serializer.data)

@extend_schema(
	tags=["Device"],
	request=ReturnSerializer, responses=ReturnSerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def return_create(request):
	serializer = ReturnSerializer(data=request.data, context={'request': request})
	if serializer.is_valid():
		serializer.save()
		return Response(serializer.data, status=status.HTTP_201_CREATED)
	return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
	tags=["Device"],
	responses=ReturnSerializer(many=True))
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def return_list(request):
	returns = Return.objects.all().order_by('-return_date')
	serializer = ReturnSerializer(returns, many=True)
	return Response(serializer.data)


@extend_schema(
	tags=["Contact"],
	request=ContactSerializer, responses=ContactSerializer)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def contact_create(request):
	serializer = ContactSerializer(data=request.data)
	if serializer.is_valid():
		serializer.save()
		return Response(serializer.data, status=status.HTTP_201_CREATED)
	return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
	tags=["Contact"],
	responses=ContactSerializer(many=True))
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def contact_list(request):
	contacts = Contact.objects.all().order_by('-created_at')
	serializer = ContactSerializer(contacts, many=True)
	return Response(serializer.data)


@extend_schema(
	tags=["Device"],
	responses=LostItemSerializer(many=True))
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def lostitem_filter_by_status(request):
	status = request.query_params.get('status', 'lost')
	items = LostItem.objects.filter(status=status).order_by('-date_reported')
	serializer = LostItemSerializer(items, many=True)
	return Response(serializer.data)


@extend_schema(
	tags=["Device"],
	responses=FoundItemSerializer(many=True))
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def founditem_filter_by_status(request):
	status = request.query_params.get('status', 'found')
	items = FoundItem.objects.filter(status=status).order_by('-date_reported')
	serializer = FoundItemSerializer(items, many=True)
	return Response(serializer.data)


@extend_schema(
	tags=["Device"],
	responses=LostItemSerializer(many=True))
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def search_by_serial_number(request):
	serial_number = request.query_params.get('serial_number')
	if not serial_number:
		return Response({'error': 'serial_number parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
	
	# Search in both lost and found items
	lost_items = LostItem.objects.filter(serial_number__icontains=serial_number)
	found_items = FoundItem.objects.filter(serial_number__icontains=serial_number)
	
	lost_serializer = LostItemSerializer(lost_items, many=True)
	found_serializer = FoundItemSerializer(found_items, many=True)
	
	return Response({
		'lost_items': lost_serializer.data,
		'found_items': found_serializer.data
	})


@extend_schema(
	tags=["Device"],
	responses=LostItemSerializer(many=True))
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_categories(request):
	from .models import CATEGORY_CHOICES
	return Response({'categories': [{'value': choice[0], 'label': choice[1]} for choice in CATEGORY_CHOICES]})

