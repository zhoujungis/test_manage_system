from rest_framework import serializers
from .models import TestRun, TestResult
from apps.testcases.serializers import TestCaseListSerializer


class TestResultSerializer(serializers.ModelSerializer):
    test_case_detail = TestCaseListSerializer(source='test_case', read_only=True)

    class Meta:
        model = TestResult
        fields = ['id', 'test_run', 'test_case', 'test_case_detail', 'status',
                  'actual_result', 'notes', 'executed_by', 'executed_at']
        read_only_fields = ['executed_by', 'executed_at']


class TestResultUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestResult
        fields = ['id', 'status', 'actual_result', 'notes']


class TestRunListSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source='test_plan.name', read_only=True)
    total = serializers.SerializerMethodField()
    passed = serializers.SerializerMethodField()
    failed = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = TestRun
        fields = ['id', 'test_plan', 'plan_name', 'name', 'status', 'total', 'passed', 'failed',
                  'assigned_to', 'started_at', 'completed_at', 'created_by_name', 'created_at']
        read_only_fields = ['created_by', 'created_at']

    def get_total(self, obj):
        return getattr(obj, 'total', obj.results.count())

    def get_passed(self, obj):
        return getattr(obj, 'passed', obj.results.filter(status='pass').count())

    def get_failed(self, obj):
        return getattr(obj, 'failed', obj.results.filter(status='fail').count())


class TestRunDetailSerializer(serializers.ModelSerializer):
    results = TestResultSerializer(many=True, read_only=True)
    plan_name = serializers.CharField(source='test_plan.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = TestRun
        fields = ['id', 'test_plan', 'plan_name', 'name', 'status', 'results',
                  'assigned_to', 'started_at', 'completed_at', 'created_by_name', 'created_at']
        read_only_fields = ['created_by', 'created_at']
