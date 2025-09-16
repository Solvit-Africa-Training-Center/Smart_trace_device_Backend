
from rest_framework import serializers
from .models import Device, LostItem, FoundItem, Match, Return, Contact

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
    serial_number = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    contact_email = serializers.EmailField(required=True)
    location = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    phone_number = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    device_image = serializers.ImageField(required=False, allow_null=True)
    
    class Meta:
        model = LostItem
        fields = [
            'id', 'name', 'category', 'description', 'color', 'serial_number', 'contact_email', 
            'location', 'phone_number', 'device_image', 'date_reported', 'user', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'date_reported', 'created_at', 'updated_at']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            validated_data['user'] = request.user
        else:
            validated_data['user'] = None
        return super().create(validated_data)

class FoundItemSerializer(serializers.ModelSerializer):
    serial_number = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    contact_email = serializers.EmailField(required=False, allow_null=True)
    location = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    phone_number = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    device_image = serializers.ImageField(required=False, allow_null=True)
    
    class Meta:
        model = FoundItem
        fields = [
            'id', 'name', 'category', 'description', 'color', 'serial_number', 'contact_email', 
            'location', 'phone_number', 'device_image', 'date_reported', 'user', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'date_reported', 'created_at', 'updated_at']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            validated_data['user'] = request.user
        else:
            validated_data['user'] = None
        return super().create(validated_data)

class MatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Match
        fields = [
            'id', 'lost_item', 'found_item', 'match_status', 'match_date'
        ]
        read_only_fields = ['id', 'match_date']

class ReturnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Return
        fields = [
            'id', 'lost_item', 'found_item', 'owner', 'finder', 'return_date', 'confirmation'
        ]
        read_only_fields = ['id', 'return_date']


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = [
            'id', 'first_name', 'last_name', 'email', 'subject', 'message', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
