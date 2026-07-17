from django.db import models
from django.contrib.auth.models import User
from apps.projects.models import Project
from apps.testcases.models import TestCase


class TestPlan(models.Model):
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('active', '执行中'),
        ('completed', '已完成'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='testplans', db_index=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', db_index=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_testplans')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'test_plan'
        # M1 fix: 删默认 ordering

    def __str__(self):
        return self.name


class TestPlanCase(models.Model):
    test_plan = models.ForeignKey(TestPlan, on_delete=models.CASCADE, related_name='plan_cases')
    test_case = models.ForeignKey(TestCase, on_delete=models.CASCADE, related_name='plan_cases')
    order = models.IntegerField(default=0)

    class Meta:
        db_table = 'test_plan_case'
        # M11 fix: plan_cases 列表按 test_plan + order 拉，加复合索引
        indexes = [
            models.Index(fields=['test_plan', 'order']),
        ]

    def __str__(self):
        return f'{self.test_plan.name} - {self.test_case.title}'
