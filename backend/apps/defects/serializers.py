from rest_framework import serializers
from .models import Defect


class DefectListSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)

    class Meta:
        model = Defect
        fields = ['id', 'project', 'project_name', 'title', 'severity', 'status',
                  'assigned_to', 'assigned_to_name', 'created_by_name', 'created_at', 'updated_at']


class DefectDetailSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)

    class Meta:
        model = Defect
        fields = ['id', 'project', 'project_name', 'test_result', 'title', 'description',
                  'severity', 'status', 'assigned_to', 'assigned_to_name',
                  'created_by', 'created_by_name', 'created_at', 'updated_at']
        read_only_fields = ['created_by', 'created_at', 'updated_at']
