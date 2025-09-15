
from drf_spectacular.utils import extend_schema
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Device, LostItem, FoundItem, Match, Return
from .Serializers import DeviceSerializer
from .Serializers import LostItemSerializer, FoundItemSerializer, MatchSerializer, ReturnSerializer

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
@permission_classes([IsAuthenticated])
def lostitem_create(request):
	serializer = LostItemSerializer(data=request.data, context={'request': request})
	if serializer.is_valid():
		serializer.save(user=request.user)
		return Response(serializer.data, status=status.HTTP_201_CREATED)
	return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
	queryset = LostItem.objects.all()
	if name:
		queryset = queryset.filter(name__icontains=name)
	if category:
		queryset = queryset.filter(category__icontains=category)
	if color:
		queryset = queryset.filter(color__icontains=color)
	serializer = LostItemSerializer(queryset, many=True)
	return Response(serializer.data)

@extend_schema(
	tags=["Device"],
	request=FoundItemSerializer, responses=FoundItemSerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def founditem_create(request):
	serializer = FoundItemSerializer(data=request.data, context={'request': request})
	if serializer.is_valid():
		serializer.save(user=request.user)
		return Response(serializer.data, status=status.HTTP_201_CREATED)
	return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
	queryset = FoundItem.objects.all()
	if name:
		queryset = queryset.filter(name__icontains=name)
	if category:
		queryset = queryset.filter(category__icontains=category)
	if color:
		queryset = queryset.filter(color__icontains=color)
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

