from rest_framework import serializers
from .models import Report

class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ['id', 'user', 'item_id', 'type', 'details', 'report_date']
        read_only_fields = ['id', 'user', 'report_date']
