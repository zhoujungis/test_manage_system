from django.db import models
from django.contrib.auth.models import User
from apps.projects.models import Project, Module


class TestCase(models.Model):
    PRIORITY_CHOICES = [
        ('P0', 'P0-最高'),
        ('P1', 'P1-高'),
        ('P2', 'P2-中'),
        ('P3', 'P3-低'),
        ('P4', 'P4-最低'),
    ]
    TYPE_CHOICES = [
        ('functional', '功能测试'),
        ('api', '接口测试'),
        ('ui', 'UI测试'),
        ('performance', '性能测试'),
    ]
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('active', '活跃'),
        ('deprecated', '已废弃'),
    ]
    PRODUCT_LINE_CHOICES = [
        ('camera', '摄像头'),
        ('doorbell', '门铃'),
    ]

    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='testcases')
    product_line = models.CharField(max_length=20, choices=PRODUCT_LINE_CHOICES, default='camera', db_index=True)
    module = models.ForeignKey(Module, on_delete=models.SET_NULL, null=True, blank=True, related_name='testcases')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='P2', db_index=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='functional', db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', db_index=True)
    preconditions = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_testcases')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_testcases')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'test_case'
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.get_priority_display()}] {self.title}'


class TestCaseStep(models.Model):
    test_case = models.ForeignKey(TestCase, on_delete=models.CASCADE, related_name='steps')
    step_number = models.IntegerField()
    action = models.TextField(blank=True, default='')
    expected_result = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'test_case_step'
        ordering = ['step_number']

    def __str__(self):
        return f'Step {self.step_number}: {self.action[:50]}'
