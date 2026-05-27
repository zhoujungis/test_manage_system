from django.db import models
from django.contrib.auth.models import User


class Project(models.Model):
    STATUS_CHOICES = [
        ('active', '活跃'),
        ('archived', '已归档'),
    ]
    PRODUCT_LINE_CHOICES = [
        ('camera', '摄像头'),
        ('doorbell', '门铃'),
    ]
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    product_line = models.CharField(max_length=20, choices=PRODUCT_LINE_CHOICES, default='camera')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='managed_projects')
    planned_start_date = models.DateField(null=True, blank=True)
    planned_end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'project'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Module(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='modules')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'module'
        ordering = ['id']

    def __str__(self):
        return self.name


class ProjectMember(models.Model):
    ROLE_CHOICES = [
        ('leader', '项目负责人'),
        ('tester', '测试人员'),
        ('developer', '开发人员'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='tester')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'project_member'
        unique_together = ['project', 'user']
        ordering = ['joined_at']

    def __str__(self):
        return f'{self.project.name} - {self.user.username} ({self.get_role_display()})'


class ProjectTask(models.Model):
    STATUS_CHOICES = [
        ('todo', '待开始'),
        ('in_progress', '进行中'),
        ('done', '已完成'),
    ]
    PRIORITY_CHOICES = [
        ('P0', 'P0-紧急'),
        ('P1', 'P1-高'),
        ('P2', 'P2-中'),
        ('P3', 'P3-低'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    round = models.CharField(max_length=50, blank=True, default='', verbose_name='提测轮次')
    description = models.TextField(blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='P2')
    due_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'project_task'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({self.get_status_display()})'


class TestCaseAssignment(models.Model):
    STATUS_CHOICES = [
        ('pending', '待测试'),
        ('passed', 'Pass'),
        ('failed', 'Fail'),
        ('not_applicable', 'N/A'),
        ('not_tested', 'N/T'),
    ]
    APPROVAL_CHOICES = [
        ('pending', '未审核'),
        ('approved', '审核通过'),
        ('rejected', '审核不通过'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='case_assignments')
    task = models.ForeignKey(ProjectTask, on_delete=models.CASCADE, null=True, blank=True, related_name='case_assignments', verbose_name='关联任务')
    test_case = models.ForeignKey('testcases.TestCase', on_delete=models.CASCADE, related_name='assignments')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='case_assignments')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approval_status = models.CharField(max_length=20, choices=APPROVAL_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_assignments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'test_case_assignment'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.test_case.title} → {self.assigned_to.username if self.assigned_to else "未分配"}'


def assignment_attachment_upload_to(instance, filename):
    return f'assignment_attachments/{instance.assignment_id}/{filename}'


class AssignmentAttachment(models.Model):
    assignment = models.ForeignKey(
        TestCaseAssignment, on_delete=models.CASCADE, related_name='attachments'
    )
    file = models.FileField(upload_to=assignment_attachment_upload_to)
    original_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(default=0)
    uploaded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='uploaded_assignment_files'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'assignment_attachment'
        ordering = ['-created_at']

    def __str__(self):
        return self.original_name
