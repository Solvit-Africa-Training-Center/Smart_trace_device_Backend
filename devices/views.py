
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
from django.db import transaction

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



from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions, status
from rest_framework.response import Response

@extend_schema(
    tags=["Device"],
    request=LostItemSerializer,
    responses=LostItemSerializer,
    examples=[],
    parameters=[
        OpenApiParameter(
            name="image",
            type=OpenApiTypes.BINARY,
            # location=OpenApiParameter.FORM,
            description="Upload image file"
        ),
        OpenApiParameter(
            name="recepiet",
            type=OpenApiTypes.BINARY,
            # location=OpenApiParameter.FORM,
            description="Upload receipt file"
        ),
    ],
    methods=["POST"]
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def lostitem_create(request):
    serializer = LostItemSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        lost_item = serializer.save()
        # Inverse matching: when a lost item is posted, check for existing found items
        serial_number = getattr(lost_item, 'serial_number', None)
        if serial_number:
            matching_found_items = FoundItem.objects.filter(serial_number=serial_number, status='found').order_by('-date_reported')
            for found_item in matching_found_items:
                # Create match record if not already exists
                if not Match.objects.filter(lost_item=lost_item, found_item=found_item).exists():
                    Match.objects.create(
                    lost_item=lost_item,
                    found_item=found_item,
                    match_status='unclaimed',
                    loster_name=' '.join([p for p in [getattr(lost_item, 'first_name', None), getattr(lost_item, 'last_name', None)] if p]) or None,
                    loster_phone_number=getattr(lost_item, 'phone_number', None),
                    loster_email=getattr(lost_item, 'loster_email', None),
                    founder_name=' '.join([p for p in [getattr(found_item, 'reporter_first_name', None), getattr(found_item, 'reporter_last_name', None)] if p]) or None,
                    founder_phone_number=getattr(found_item, 'phone_number', None),
                    founder_email=getattr(found_item, 'founder_email', None) or getattr(found_item, 'contact_email', None),
                    device_name=getattr(found_item, 'name', None) or getattr(lost_item, 'title', None),
                    serial_number=serial_number,
                    )
                # Notify both parties if emails are present
                if getattr(lost_item, 'loster_email', None):
                    try:
                        subject = 'Possible Match Found for Your Lost Item'
                        message = (
                            f"Hello {lost_item.first_name or 'there'},\n\n"
                            f"We found a reported found item with the same serial number ({serial_number}).\n"
                            f"Found item: {found_item.name} in category {found_item.category}.\n\n"
                            f"Please contact us to verify and arrange collection.\n\n"
                            f"Best regards,\n"
                            f"Lost & Found Team"
                        )
                        send_mail(subject, message, getattr(settings, 'DEFAULT_FROM_EMAIL', None), [lost_item.loster_email], fail_silently=True)
                    except Exception as e:
                        print(f"Failed to send email to loster: {e}")
                if getattr(found_item, 'founder_email', None):
                    try:
                        subject = 'Potential Owner Located for the Found Item'
                        message = (
                            f"Hello,\n\n"
                            f"A lost report matching the serial number ({serial_number}) was posted.\n"
                            f"Lost item title: {getattr(lost_item, 'title', 'Unknown')}.\n\n"
                            f"We will facilitate contact to verify ownership.\n\n"
                            f"Best regards,\n"
                            f"Lost & Found Team"
                        )
                        send_mail(subject, message, getattr(settings, 'DEFAULT_FROM_EMAIL', None), [found_item.founder_email], fail_silently=True)
                    except Exception as e:
                        print(f"Failed to send email to founder: {e}")
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
        previous_status = item.status
        updated_item = serializer.save()
        new_status = updated_item.status
        # Enforce simple status transitions and side effects
        if new_status != previous_status:
            allowed = {
                'lost': ['claimed'],
                'claimed': [],
                'found': ['claimed'],
            }
            if previous_status in allowed and new_status not in allowed[previous_status]:
                # revert and inform client
                updated_item.status = previous_status
                updated_item.save(update_fields=['status'])
                return Response({'detail': 'Invalid status transition'}, status=status.HTTP_400_BAD_REQUEST)

            # If transitioning to claimed, mark matched counterparts as claimed too
            if new_status == 'claimed':
                serial_number = getattr(updated_item, 'serial_number', None)
                if serial_number:
                    matched_found = FoundItem.objects.filter(serial_number=serial_number)
                    matched_found.update(status='claimed')
        return Response(LostItemSerializer(updated_item).data)
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
			# Check for matching lost items with same serial number
			matching_lost_items = LostItem.objects.filter(serial_number=serial_number, status='lost').order_by('-date_reported')
			
			for lost_item in matching_lost_items:
				# Create match record with default unclaimed status
				Match.objects.create(
                    lost_item=lost_item,
                    found_item=found_item,
                    match_status='unclaimed',
                    loster_name=' '.join([p for p in [getattr(lost_item, 'first_name', None), getattr(lost_item, 'last_name', None)] if p]) or None,
                    loster_phone_number=getattr(lost_item, 'phone_number', None),
                    loster_email=getattr(lost_item, 'loster_email', None),
                    founder_name=' '.join([p for p in [getattr(found_item, 'reporter_first_name', None), getattr(found_item, 'reporter_last_name', None)] if p]) or None,
                    founder_phone_number=getattr(found_item, 'phone_number', None),
                    founder_email=getattr(found_item, 'founder_email', None) or getattr(found_item, 'contact_email', None),
                    device_name=getattr(found_item, 'name', None) or getattr(lost_item, 'title', None),
                    serial_number=serial_number,
                )
				
				# Send email to loster if email is provided
				if getattr(lost_item, 'loster_email', None):
					try:
						subject = 'Good News! Your Lost Item May Have Been Found'
						message = (
							f"Hello {lost_item.first_name or 'there'},\n\n"
							f"We have great news! A found item with serial number {serial_number} "
							f"has been reported that matches your lost {lost_item.title}.\n\n"
							f"Found item details:\n"
							f"- Name: {found_item.name}\n"
							f"- Category: {found_item.category}\n"
							f"- Description: {found_item.description or 'No description provided'}\n\n"
							f"Please contact us to verify if this is your item and arrange for pickup.\n\n"
							f"Best regards,\n"
							f"Lost & Found Team"
						)
						send_mail(subject, message, getattr(settings, 'DEFAULT_FROM_EMAIL', None), [lost_item.loster_email], fail_silently=False)
					except Exception as e:
						print(f"Failed to send email to loster: {e}")
				
				# Send email to founder if email is provided
				if getattr(found_item, 'founder_email', None):
					try:
						subject = 'Thank You! Your Found Item Report May Help Someone'
						message = (
							f"Hello {(getattr(found_item, 'reporter_first_name', None) or 'there')},\n\n"
							f"Thank you for reporting the found item: {found_item.name}.\n\n"
							f"We found a potential match with a lost item that has the same serial number ({serial_number}).\n"
							f"The owner has been notified and may contact us soon.\n\n"
							f"Please keep the item safe until we can arrange for verification and return.\n\n"
							f"Thank you for your kindness!\n\n"
							f"Best regards,\n"
							f"Lost & Found Team"
						)
						send_mail(subject, message, getattr(settings, 'DEFAULT_FROM_EMAIL', None), [found_item.founder_email], fail_silently=False)
					except Exception as e:
						print(f"Failed to send email to founder: {e}")
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
        previous_status = item.status
        updated_item = serializer.save()
        new_status = updated_item.status
        # Enforce simple status transitions and side effects
        if new_status != previous_status:
            allowed = {
                'found': ['claimed'],
                'claimed': [],
                'lost': ['claimed'],
            }
            if previous_status in allowed and new_status not in allowed[previous_status]:
                updated_item.status = previous_status
                updated_item.save(update_fields=['status'])
                return Response({'detail': 'Invalid status transition'}, status=status.HTTP_400_BAD_REQUEST)

            if new_status == 'claimed':
                serial_number = getattr(updated_item, 'serial_number', None)
                if serial_number:
                    matched_lost = LostItem.objects.filter(serial_number=serial_number)
                    matched_lost.update(status='claimed')
        return Response(FoundItemSerializer(updated_item).data)
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
		match = serializer.save()
		# Ensure default status if not provided
		if not match.match_status:
			match.match_status = 'unclaimed'
			match.save(update_fields=['match_status'])
		return Response(MatchSerializer(match).data, status=status.HTTP_201_CREATED)
	return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
	tags=["Device"],
	responses=MatchSerializer(many=True))
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def match_list(request):
    matches = Match.objects.select_related('lost_item', 'found_item').all().order_by('-match_date')
    serializer = MatchSerializer(matches, many=True)
    return Response(serializer.data)


@extend_schema(
    tags=["Device"],
    responses=MatchSerializer,
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def claim_match(request):
    match_id = request.data.get('match_id')
    if not match_id:
        return Response({'detail': 'match_id is required'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        match = Match.objects.select_related('lost_item', 'found_item').get(id=match_id)
    except Match.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    if match.match_status == 'claimed':
        return Response({'detail': 'Already claimed'}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        match.match_status = 'claimed'
        match.save(update_fields=['match_status'])

        # Update item statuses
        if match.lost_item:
            match.lost_item.status = 'claimed'
            match.lost_item.save(update_fields=['status'])
        if match.found_item:
            match.found_item.status = 'claimed'
            match.found_item.save(update_fields=['status'])

        # Create Return record
        owner = match.lost_item.user if match.lost_item and match.lost_item.user else None
        finder = match.found_item.user if match.found_item and match.found_item.user else None
        Return.objects.create(
            lost_item=match.lost_item,
            found_item=match.found_item,
            owner=owner,
            finder=finder,
            confirmation=True,
            claimed_by=request.user,
            notes=request.data.get('notes'),
            owner_email=getattr(match.lost_item, 'loster_email', None),
            owner_name=' '.join([p for p in [getattr(match.lost_item, 'first_name', None), getattr(match.lost_item, 'last_name', None)] if p]) or None,
            finder_email=getattr(match.found_item, 'founder_email', None),
            finder_name=' '.join([p for p in [getattr(match.found_item, 'reporter_first_name', None), getattr(match.found_item, 'reporter_last_name', None)] if p]) or None,
        )

    return Response(MatchSerializer(match).data)


@extend_schema(
    tags=["Device"],
    responses=MatchSerializer,
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def match_detail(request, id):
    try:
        match = Match.objects.select_related('lost_item', 'found_item').get(id=id)
    except Match.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
    return Response(MatchSerializer(match).data)


@extend_schema(
    tags=["Device"],
    responses=None,
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def match_delete(request, id):
    try:
        match = Match.objects.get(id=id)
    except Match.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
    match.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=["Device"],
    request=None,
    parameters=[
        OpenApiParameter(name='email', description='Owner email', required=True, type=OpenApiTypes.STR),
    ],
    responses=LostItemSerializer(many=True),
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def lostitem_by_email(request):
    email = request.query_params.get('email')
    if not email:
        return Response({'error': 'email query parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
    items = LostItem.objects.filter(loster_email=email).order_by('-date_reported')
    return Response(LostItemSerializer(items, many=True).data)


@extend_schema(
    tags=["Device"],
    request=None,
    parameters=[
        OpenApiParameter(name='email', description='Finder email', required=True, type=OpenApiTypes.STR),
    ],
    responses=FoundItemSerializer(many=True),
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def founditem_by_email(request):
    email = request.query_params.get('email')
    if not email:
        return Response({'error': 'email query parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
    items = FoundItem.objects.filter(founder_email=email).order_by('-date_reported')
    return Response(FoundItemSerializer(items, many=True).data)

@extend_schema(
	tags=["Device"],
	request=ReturnSerializer, responses=ReturnSerializer)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
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
	tags=["Contact"],
	responses=None)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def contact_delete(request, id):
	try:
		contact = Contact.objects.get(id=id)
	except Contact.DoesNotExist:
		return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
	contact.delete()
	return Response(status=status.HTTP_204_NO_CONTENT)


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

