from rest_framework import serializers
from .models import TestCase, TestCaseStep


class TestCaseStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestCaseStep
        fields = ['id', 'step_number', 'action', 'expected_result']


class TestCaseListSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True, default=None)
    module_name = serializers.CharField(source='module.name', read_only=True, default=None)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True)

    class Meta:
        model = TestCase
        fields = ['id', 'title', 'description', 'project', 'project_name', 'module', 'module_name',
                  'priority', 'type', 'status', 'product_line', 'created_by', 'created_by_name',
                  'updated_by', 'updated_by_name', 'created_at', 'updated_at']


class TestCaseDetailSerializer(serializers.ModelSerializer):
    steps = TestCaseStepSerializer(many=True)
    module_name = serializers.CharField(source='module.name', read_only=True, default=None)
    project_name = serializers.CharField(source='project.name', read_only=True, default=None)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True)

    class Meta:
        model = TestCase
        fields = ['id', 'project', 'project_name', 'module', 'module_name', 'title', 'description',
                  'priority', 'type', 'status', 'product_line', 'preconditions', 'steps',
                  'created_by', 'created_by_name', 'updated_by', 'updated_by_name',
                  'created_at', 'updated_at']
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'updated_by']

    def create(self, validated_data):
        steps_data = validated_data.pop('steps', [])
        testcase = TestCase.objects.create(**validated_data)
        for step in steps_data:
            TestCaseStep.objects.create(test_case=testcase, **step)
        return testcase

    def update(self, instance, validated_data):
        from django.db import transaction
        steps_data = validated_data.pop('steps', None)
        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            if steps_data is not None:
                instance.steps.all().delete()
                for step in steps_data:
                    TestCaseStep.objects.create(test_case=instance, **step)
        return instance
