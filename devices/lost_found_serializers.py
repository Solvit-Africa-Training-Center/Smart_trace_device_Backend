from rest_framework import serializers
from .models import LostItem, FoundItem

class LostItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = LostItem
        fields = [
            'id', 'name', 'category', 'description', 'color', 'date_reported',
            'user', 'device', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'date_reported', 'created_at', 'updated_at', 'status']

class FoundItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoundItem
        fields = [
            'id', 'name', 'category', 'description', 'color', 'date_reported',
            'user', 'device', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'date_reported', 'created_at', 'updated_at', 'status']
