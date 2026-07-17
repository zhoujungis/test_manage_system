from rest_framework import serializers
from .models import TestCase, TestCaseStep

# Sentinel：区分"客户端没传 steps 字段"与"客户端传了 steps=[]"
_UNSET = object()


class TestCaseStepSerializer(serializers.ModelSerializer):
    # C2 fix: 显式覆盖 id 让其可写。DRF 默认把 PK 设为 read_only，会剥掉
    # 客户端传来的 step.id → update 里 step.get('id') 永远是 None → 旧步骤
    # 全部被识别为新增，再被 .steps.exclude(id__in=keep_ids).delete() 删光。
    # 加上 allow_null=True 让"前端新增的步骤（没 id）"也能通过校验。
    id = serializers.IntegerField(required=False, allow_null=True)

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
                  'priority', 'case_type', 'status', 'product_line', 'created_by', 'created_by_name',
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
                  'priority', 'case_type', 'status', 'product_line', 'preconditions', 'steps',
                  'created_by', 'created_by_name', 'updated_by', 'updated_by_name',
                  'created_at', 'updated_at']
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'updated_by']

    def create(self, validated_data):
        # M9 fix: 用例 + 步骤原子创建 —— 步骤失败不留只有标题没有步骤的孤儿用例
        from django.db import transaction
        steps_data = validated_data.pop('steps', [])
        with transaction.atomic():
            testcase = TestCase.objects.create(**validated_data)
            for step in steps_data:
                TestCaseStep.objects.create(test_case=testcase, **step)
        return testcase

    def update(self, instance, validated_data):
        """diff-and-upsert 测试步骤：
        - 传 'steps' 字段（list）→ 整替换（diff 入库）
        - 不传 'steps' 字段 → 不动步骤（保留 id / created_at）
        - 传 'steps': [] → 清空所有步骤

        与原实现"全删全建"相比保留：
        - 步骤主键（任何外键引用都不会断）
        - created_at（审计）
        - 单次往返（N+1 → 1 次 SELECT + 1 次 bulk diff）
        """
        from django.db import transaction
        steps_data = validated_data.pop('steps', _UNSET)
        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            if steps_data is not _UNSET:
                existing = {s.id: s for s in instance.steps.all()}
                keep_ids = set()
                for step in steps_data:
                    sid = step.get('id')
                    payload = {k: v for k, v in step.items() if k != 'id'}
                    if sid and sid in existing:
                        row = existing[sid]
                        for k, v in payload.items():
                            setattr(row, k, v)
                        row.save()
                        keep_ids.add(sid)
                    else:
                        new = TestCaseStep.objects.create(test_case=instance, **payload)
                        keep_ids.add(new.id)
                # 仅删除客户端明确删除的步骤
                if existing:
                    instance.steps.exclude(id__in=keep_ids).delete()
        return instance
