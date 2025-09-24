from rest_framework import serializers
from .models import Match, Return

class LostFoundByEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()

class MatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Match
        fields = ['id', 'lost_item', 'found_item', 'match_status', 'match_date']
        read_only_fields = ['id', 'match_date']

class ReturnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Return
        fields = ['id', 'lost_item', 'found_item', 'owner', 'finder', 'return_date', 'confirmation']
        read_only_fields = ['id', 'return_date']
