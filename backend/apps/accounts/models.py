import hashlib
import secrets

from django.db import models
from django.contrib.auth.models import User


def hash_verification_code(code: str) -> str:
    """对验证码做 SHA-256 哈希；存库用 hash，避免明文落入备份/日志。

    6 位十进制码的熵约 20 bit —— 哈希不能增加熵，只是减小泄漏面。
    真正的安全靠 attempts 上限 + throttle + 短 TTL 来补。
    """
    return hashlib.sha256(code.encode('utf-8')).hexdigest()


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
    # D8 fix: 默认 False（fail-closed）。权限按角色授权时由 apply_role_default_permissions()
    # 显式打开；忘调 apply_role_default_permissions() 的代码路径也不会无脑放行。
    can_access_projects = models.BooleanField(default=False, verbose_name='项目管理')
    can_access_testcase_library = models.BooleanField(default=False, verbose_name='测试用例库')
    can_manage_testcase_library = models.BooleanField(default=False, verbose_name='管理用例库')
    can_access_my_projects = models.BooleanField(default=False, verbose_name='我的项目')

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
    """邮箱验证码（C3 重写）。

    - 不再存明文验证码：code_hash = SHA-256(code)
    - purpose 区分 'register' / 'reset'，避免用注册码去重置
    - attempts 累计验证失败次数，>= MAX_ATTEMPTS 即锁定
    - consumed_at 取代 is_used；NULL 表示未消费
    """
    PURPOSE_REGISTER = 'register'
    PURPOSE_RESET = 'reset'
    PURPOSE_CHOICES = [
        (PURPOSE_REGISTER, '注册'),
        (PURPOSE_RESET, '重置'),
    ]
    MAX_ATTEMPTS = 5
    CODE_LENGTH = 6
    # C9 fix: 单一来源。views.py 不再硬编码 timedelta(minutes=5)。
    CODE_TTL_SECONDS = 5 * 60

    email = models.EmailField(db_index=True)
    purpose = models.CharField(max_length=16, choices=PURPOSE_CHOICES)
    code_hash = models.CharField(max_length=128)
    attempts = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    consumed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'verification_code'
        indexes = [
            models.Index(fields=['email', 'purpose', 'consumed_at']),
        ]

    def __str__(self):
        return f'{self.email} {self.purpose} attempts={self.attempts}'

    @property
    def is_locked(self):
        return self.attempts >= self.MAX_ATTEMPTS

    @property
    def is_active(self):
        """未消费 + 未过期 + 未锁定。"""
        from django.utils import timezone
        if self.consumed_at is not None or self.is_locked:
            return False
        return (timezone.now() - self.created_at).total_seconds() < self.CODE_TTL_SECONDS

    @classmethod
    def issue(cls, email: str, purpose: str):
        """生成一段强随机验证码并落库（哈希），返回明文供邮件发送。"""
        from django.utils import timezone
        # 旧的同一 email + purpose 未消费码全部作废
        cls.objects.filter(
            email=email, purpose=purpose, consumed_at__isnull=True,
        ).update(consumed_at=timezone.now())
        code = ''.join(
            str(secrets.randbelow(10)) for _ in range(cls.CODE_LENGTH)
        )
        cls.objects.create(
            email=email,
            purpose=purpose,
            code_hash=hash_verification_code(code),
        )
        return code

    def record_failure(self):
        """验证失败时累加 attempts。"""
        VerificationCode.objects.filter(pk=self.pk).update(attempts=models.F('attempts') + 1)
