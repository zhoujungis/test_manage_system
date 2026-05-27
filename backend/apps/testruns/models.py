from django.db import models
from django.contrib.auth.models import User
from apps.testplans.models import TestPlan
from apps.testcases.models import TestCase


class TestRun(models.Model):
    STATUS_CHOICES = [
        ('pending', '待执行'),
        ('running', '执行中'),
        ('completed', '已完成'),
    ]
    test_plan = models.ForeignKey(TestPlan, on_delete=models.CASCADE, related_name='testruns', db_index=True)
    name = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_runs')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_testruns')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'test_run'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class TestResult(models.Model):
    STATUS_CHOICES = [
        ('pending', '待执行'),
        ('pass', '通过'),
        ('fail', '失败'),
        ('blocked', '阻塞'),
        ('skip', '跳过'),
    ]
    test_run = models.ForeignKey(TestRun, on_delete=models.CASCADE, related_name='results')
    test_case = models.ForeignKey(TestCase, on_delete=models.CASCADE, related_name='results')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    actual_result = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    executed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='executed_results')
    executed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'test_result'
        unique_together = ['test_run', 'test_case']

    def __str__(self):
        return f'{self.test_case.title} - {self.get_status_display()}'
