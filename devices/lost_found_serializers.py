from rest_framework import serializers
from .models import LostItem, FoundItem, Device

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
        read_only_fields = ['id', 'user', 'date_reported', 'created_at', 'updated_at', 'status']
    
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
        read_only_fields = ['id', 'user', 'date_reported', 'created_at', 'updated_at', 'status']
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            validated_data['user'] = request.user
        else:
            validated_data['user'] = None
        return super().create(validated_data)
