from django.db import models
from django.contrib.auth.models import User
from apps.projects.models import Project
from apps.testruns.models import TestResult


class Defect(models.Model):
    SEVERITY_CHOICES = [
        ('S0', 'S0-致命'),
        ('S1', 'S1-严重'),
        ('S2', 'S2-一般'),
        ('S3', 'S3-轻微'),
        ('S4', 'S4-建议'),
    ]
    STATUS_CHOICES = [
        ('open', '未处理'),
        ('in_progress', '处理中'),
        ('resolved', '已修复'),
        ('closed', '已关闭'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='defects', db_index=True)
    test_result = models.ForeignKey(TestResult, on_delete=models.SET_NULL, null=True, blank=True, related_name='defects')
    title = models.CharField(max_length=200)
    description = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='S2', db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open', db_index=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_defects')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_defects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'defect'
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.get_severity_display()}] {self.title}'
