
from rest_framework import serializers
from .models import Device, LostItem, FoundItem, Match, Return

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
    class Meta:
        model = LostItem
        fields = [
            'id', 'name', 'category', 'description', 'color', 'date_reported',
            'user', 'device', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'date_reported', 'created_at', 'updated_at']

class FoundItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoundItem
        fields = [
            'id', 'name', 'category', 'description', 'color', 'date_reported',
            'user', 'device', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'date_reported', 'created_at', 'updated_at']

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
