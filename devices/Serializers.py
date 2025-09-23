
from rest_framework import serializers
from django.core.files.uploadedfile import UploadedFile
from .models import Device, LostItem, FoundItem, Match, Return, Contact
from rest_framework import serializers as rf_serializers

class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = [
            'id', 'user', 'serial_number', 'name', 'category', 'brand', 'color',
            'description', 'device_image', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def validate_serial_number(self, value):
        user = self.context['request'].user
        if Device.objects.filter(user=user, serial_number=value).exists():
            raise serializers.ValidationError('You already registered a device with this serial number.')
        return value

class LostItemSerializer(serializers.ModelSerializer):
    # Expose exactly the new model fields with frontend keys
    title = serializers.CharField()
    dateFound = serializers.DateField(source='date_found', required=False, allow_null=True)
    category = serializers.CharField()
    timeFound = serializers.TimeField(source='time_found', required=False, allow_null=True)
    brand = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    image = serializers.ImageField(required=False, allow_null=True)
    recepiet = serializers.FileField(required=False, allow_null=True)
    additionalInfo = serializers.CharField(source='additional_info', required=False, allow_blank=True, allow_null=True)
    addressType = serializers.CharField(source='address_type', required=False, allow_blank=True, allow_null=True)
    state = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    cityTown = serializers.CharField(source='city_town', required=False, allow_blank=True, allow_null=True)
    serialNumber = serializers.CharField(source='serial_number', required=False, allow_blank=True, allow_null=True)
    firstName = serializers.CharField(source='first_name', required=False, allow_blank=True, allow_null=True)
    lastName = serializers.CharField(source='last_name', required=False, allow_blank=True, allow_null=True)
    phoneNumber = serializers.CharField(source='phone_number', required=False, allow_blank=True, allow_null=True)
    losterEmail = serializers.EmailField(source='loster_email', required=False, allow_null=True)

    class Meta:
        model = LostItem
        fields = [
            'id',
            'title', 'dateFound', 'category', 'timeFound', 'brand', 'image', 'recepiet',
            'additionalInfo', 'addressType', 'state', 'cityTown', 'serialNumber',
            'firstName', 'lastName', 'phoneNumber', 'losterEmail',
            'date_reported', 'user', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'date_reported', 'created_at', 'updated_at', 'status']

    def to_internal_value(self, data):
        data = data.copy()
        # Normalize non-file submissions for file fields
        for key in ['image', 'recepiet']:
            if key in data and not isinstance(data[key], UploadedFile):
                if data[key] in (None, '', 'null'):
                    data[key] = None
                else:
                    # Ignore non-file string to avoid validation errors
                    data.pop(key)
        return super().to_internal_value(data)

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            validated_data['user'] = request.user
        else:
            validated_data['user'] = None
        return super().create(validated_data)

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            validated_data['user'] = request.user
        else:
            validated_data['user'] = None
        return super().create(validated_data)

class FoundItemSerializer(serializers.ModelSerializer):
    # Expose fields with exact frontend keys
    serialnumber = serializers.CharField(source='serial_number', required=False, allow_blank=True, allow_null=True)
    founderEmail = serializers.EmailField(source='founder_email', required=False, allow_null=True)
    phoneNumber = serializers.CharField(source='phone_number', required=False, allow_blank=True, allow_null=True)
    firstName = serializers.CharField(source='reporter_first_name', required=False, allow_blank=True, allow_null=True)
    lastName = serializers.CharField(source='reporter_last_name', required=False, allow_blank=True, allow_null=True)
    deviceimage = serializers.ImageField(source='device_image', required=False, allow_null=True)

    class Meta:
        model = FoundItem
        fields = [
            'id', 'name', 'category', 'description',
            'serialnumber', 'founderEmail', 'location', 'phoneNumber', 'firstName', 'address', 'province', 'district', 'lastName', 'deviceimage',
            'date_reported', 'user', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'date_reported', 'created_at', 'updated_at', 'status']

    def to_internal_value(self, data):
        data = data.copy()
        # Normalize non-file submissions for device image
        if 'deviceimage' in data and not isinstance(data['deviceimage'], UploadedFile):
            if data['deviceimage'] in (None, '', 'null'):
                data['deviceimage'] = None
            else:
                data.pop('deviceimage')
        # Compose location
        if not data.get('location'):
            parts = [
                data.get('address'),
                data.get('district'),
                data.get('province'),
            ]
            combined = ", ".join([p for p in parts if p])
            if combined:
                data['location'] = combined
        return super().to_internal_value(data)

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        return {
            'id': rep.get('id'),
            'name': rep.get('name'),
            'category': rep.get('category'),
            'description': rep.get('description'),
            'serialnumber': rep.get('serialnumber'),
            'founderEmail': rep.get('founderEmail'),
            'location': rep.get('location'),
            'phoneNumber': rep.get('phoneNumber'),
            'firstName': rep.get('firstName'),
            'address': rep.get('address'),
            'province': rep.get('province'),
            'district': rep.get('district'),
            'lastName': rep.get('lastName'),
            'deviceimage': rep.get('deviceimage'),
        }

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            validated_data['user'] = request.user
        else:
            validated_data['user'] = None
        return super().create(validated_data)

class MatchSerializer(serializers.ModelSerializer):
    # Accept input for creating matches while keeping response concise
    lost_item = serializers.PrimaryKeyRelatedField(queryset=LostItem.objects.all(), write_only=True, required=False)
    found_item = serializers.PrimaryKeyRelatedField(queryset=FoundItem.objects.all(), write_only=True, required=False)
    matched = serializers.SerializerMethodField()
    # Expose snapshot fields
    loster_name = serializers.CharField(read_only=True)
    loster_phone_number = serializers.CharField(read_only=True)
    loster_email = serializers.EmailField(read_only=True)
    founder_name = serializers.CharField(read_only=True)
    founder_phone_number = serializers.CharField(read_only=True)
    founder_email = serializers.EmailField(read_only=True)
    device_name = serializers.CharField(read_only=True)
    serial_number = serializers.CharField(read_only=True)

    class Meta:
        model = Match
        fields = [
            'id', 'match_status', 'match_date', 'matched',
            'loster_name', 'loster_phone_number', 'loster_email',
            'founder_name', 'founder_phone_number', 'founder_email',
            'device_name', 'serial_number',
            'lost_item', 'found_item'
        ]
        read_only_fields = [
            'id', 'match_date',
            'loster_name', 'loster_phone_number', 'loster_email',
            'founder_name', 'founder_phone_number', 'founder_email',
            'device_name', 'serial_number'
        ]

    def get_matched(self, obj):
        lost = obj.lost_item
        found = obj.found_item
        loster = {
            'name': ' '.join([p for p in [getattr(lost, 'first_name', None), getattr(lost, 'last_name', None)] if p]) or None,
            'phone_number': getattr(lost, 'phone_number', None),
            'email': getattr(lost, 'loster_email', None),
        }
        founder = {
            'name': ' '.join([p for p in [getattr(found, 'reporter_first_name', None), getattr(found, 'reporter_last_name', None)] if p]) or None,
            'phone_number': getattr(found, 'phone_number', None),
            'email': getattr(found, 'founder_email', None) or getattr(found, 'contact_email', None),
        }
        device_name = getattr(found, 'name', None) or getattr(lost, 'title', None)
        serial_number = getattr(found, 'serial_number', None) or getattr(lost, 'serial_number', None)
        return {
            'loster': loster,
            'founder': founder,
            'device_name': device_name,
            'serial_number': serial_number,
        }

class ReturnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Return
        fields = [
            'id', 'lost_item', 'found_item',
            'owner', 'finder', 'owner_email', 'owner_name', 'finder_email', 'finder_name',
            'return_date', 'confirmation', 'claimed_at', 'claimed_by', 'notes'
        ]
        read_only_fields = ['id', 'return_date', 'claimed_at']


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = [
            'id', 'first_name', 'last_name', 'email', 'subject', 'message', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def to_internal_value(self, data):
        # accept camelCase variants if sent by clients
        data = data.copy()
        if 'firstName' in data and 'first_name' not in data:
            data['first_name'] = data.get('firstName')
        if 'lastName' in data and 'last_name' not in data:
            data['last_name'] = data.get('lastName')
        return super().to_internal_value(data)


# Lightweight input serializers for email-based lookups
class EmailQuerySerializer(rf_serializers.Serializer):
    email = rf_serializers.EmailField(required=False)


class LostByEmailInputSerializer(EmailQuerySerializer):
    losterEmail = rf_serializers.EmailField(required=False)


class FoundByEmailInputSerializer(EmailQuerySerializer):
    founderEmail = rf_serializers.EmailField(required=False)
