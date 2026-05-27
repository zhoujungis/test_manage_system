from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', '管理员'),
        ('tester', '测试工程师'),
        ('developer', '测试开发工程师'),
        ('viewer', '观察者'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='tester')
    phone = models.CharField(max_length=20, blank=True)
    can_access_projects = models.BooleanField(default=True, verbose_name='项目管理')
    can_access_testcase_library = models.BooleanField(default=True, verbose_name='测试用例库')
    can_manage_testcase_library = models.BooleanField(default=True, verbose_name='管理用例库')
    can_access_my_projects = models.BooleanField(default=True, verbose_name='我的项目')

    class Meta:
        db_table = 'user_profile'

    def __str__(self):
        return f'{self.user.username} - {self.get_role_display()}'


ROLE_DEFAULT_PERMISSIONS = {
    'admin': {
        'can_access_projects': True,
        'can_access_testcase_library': True,
        'can_manage_testcase_library': True,
        'can_access_my_projects': True,
    },
    'tester': {
        'can_access_projects': False,
        'can_access_testcase_library': True,
        'can_manage_testcase_library': False,
        'can_access_my_projects': True,
    },
    'developer': {
        'can_access_projects': True,
        'can_access_testcase_library': True,
        'can_manage_testcase_library': True,
        'can_access_my_projects': True,
    },
    'viewer': {
        'can_access_projects': True,
        'can_access_testcase_library': True,
        'can_manage_testcase_library': False,
        'can_access_my_projects': True,
    },
}


def apply_role_default_permissions(profile, role=None):
    """按角色写入默认权限开关（管理员由调用方保证不降级）。"""
    role = role or profile.role
    defaults = ROLE_DEFAULT_PERMISSIONS.get(role, ROLE_DEFAULT_PERMISSIONS['tester'])
    for key, value in defaults.items():
        setattr(profile, key, value)
    return profile


class VerificationCode(models.Model):
    email = models.EmailField()
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    class Meta:
        db_table = 'verification_code'
