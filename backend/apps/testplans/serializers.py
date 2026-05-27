from rest_framework import serializers
from .models import TestPlan, TestPlanCase
from apps.testcases.serializers import TestCaseListSerializer


class TestPlanCaseSerializer(serializers.ModelSerializer):
    test_case_detail = TestCaseListSerializer(source='test_case', read_only=True)

    class Meta:
        model = TestPlanCase
        fields = ['id', 'test_plan', 'test_case', 'order', 'test_case_detail']


class TestPlanListSerializer(serializers.ModelSerializer):
    case_count = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = TestPlan
        fields = ['id', 'project', 'name', 'description', 'status', 'case_count',
                  'start_date', 'end_date', 'created_by', 'created_by_name', 'created_at']
        read_only_fields = ['created_by', 'created_at']

    def get_case_count(self, obj):
        return getattr(obj, 'case_count', obj.plan_cases.count())


class TestPlanDetailSerializer(serializers.ModelSerializer):
    plan_cases = TestPlanCaseSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = TestPlan
        fields = ['id', 'project', 'name', 'description', 'status', 'plan_cases',
                  'start_date', 'end_date', 'created_by', 'created_by_name', 'created_at']
        read_only_fields = ['created_by', 'created_at']
