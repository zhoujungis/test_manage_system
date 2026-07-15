from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import UserProfile, apply_role_default_permissions


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    email = serializers.EmailField(required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop('username', None)

    def validate(self, attrs):
        email = attrs.get('email', '').strip()
        password = attrs.get('password', '')

        # H4 fix: 用 iexact 大小写不敏感 + 始终跑 PBKDF2 哈希，让"未知邮箱"和"已知错误密码"
        # 两条路径的 wall-clock 一致，避免 attacker 通过时间差枚举已注册邮箱。
        from django.contrib.auth.hashers import check_password, make_password
        DUMMY_HASH = make_password('', hasher='default')

        user = User.objects.filter(email__iexact=email).first()
        active_user = user if (user and user.is_active) else None

        # 永远跑一次哈希 — 即使 user 是 None 也对照 DUMMY_HASH，让时长与已知用户一致
        if active_user is not None:
            hash_valid = active_user.check_password(password)
            authenticated = active_user if hash_valid else None
        else:
            check_password(password, DUMMY_HASH)
            authenticated = None

        if not authenticated:
            raise serializers.ValidationError('邮箱或密码错误')

        refresh = self.get_token(authenticated)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            'role', 'phone',
            'can_access_projects', 'can_access_testcase_library',
            'can_manage_testcase_library', 'can_access_my_projects',
        ]


class UserSerializer(serializers.ModelSerializer):
    """用户详情（M1 fix：去掉 N+1、去掉读取路径上的 get_or_create）。

    设计要点：
    - 每个 UserSerializer 实例上挂一份 _profile_cache，
      同一实例内 get_* 多次访问 user.profile 只查一次。
    - 读取路径不再调 UserProfile.objects.get_or_create(...)，
      避免无意中写入；后台用 signals 创建 profile。
    - 假定调用方用 select_related('profile') 取数；否则单条记录自动回退到一次查询。
    - 列表（many=True）期间 DRF 会对每条记录新开一个 serializer 实例，
      缓存不会跨记录共享 —— 但每条记录内仍只走一次 DB。
    """

    profile = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    role_label = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'date_joined', 'is_active',
            'profile', 'role', 'role_label', 'phone', 'permissions', 'is_admin',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._profile_cache = {}

    def _get_profile(self, user):
        pk = user.pk
        if pk in self._profile_cache:
            return self._profile_cache[pk]
        # 优先用 select_related('profile') 已经 pre-fetch 的对象
        cached = getattr(user, '_profile_cache', None)  # 兼容 view 注入
        if cached is not None:
            self._profile_cache[pk] = cached
            return cached
        try:
            profile = user.profile
        except UserProfile.DoesNotExist:
            profile = None
        else:
            self._profile_cache[pk] = profile
            return profile
        # 兜底单条查询，且不再静默创建 —— 留给 signals / 后台创建
        try:
            profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            profile = None
        self._profile_cache[pk] = profile
        return profile

    def _missing_profile(self, user):
        # 用于序列化降级：profile 缺失时返回中性元数据，而不是 500
        return {
            'role': '',
            'phone': '',
            'can_access_projects': False,
            'can_access_testcase_library': False,
            'can_manage_testcase_library': False,
            'can_access_my_projects': False,
        }

    def get_profile(self, user):
        profile = self._get_profile(user)
        if profile is None:
            return self._missing_profile(user)
        return UserProfileSerializer(profile).data

    def get_role(self, user):
        profile = self._get_profile(user)
        return profile.role if profile else ''

    def get_role_label(self, user):
        profile = self._get_profile(user)
        return profile.get_role_display() if profile else ''

    def get_phone(self, user):
        profile = self._get_profile(user)
        return profile.phone if profile and profile.phone else ''

    def get_permissions(self, user):
        from .permissions import get_user_permissions
        return get_user_permissions(user)

    def get_is_admin(self, user):
        from .permissions import is_admin
        return is_admin(user)


class AdminUserPermissionSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, required=False)
    can_access_projects = serializers.BooleanField(required=False)
    can_access_testcase_library = serializers.BooleanField(required=False)
    can_manage_testcase_library = serializers.BooleanField(required=False)
    can_access_my_projects = serializers.BooleanField(required=False)
    apply_role_defaults = serializers.BooleanField(required=False, default=False)

    def validate_role(self, value):
        if value == 'admin':
            raise serializers.ValidationError('不能通过此接口设置为管理员')
        return value


class ChangePasswordSerializer(serializers.Serializer):
    # SECURITY: 不再接受 email 字段；用户由视图从 request.user 注入，
    # 避免任何登录用户可改任意账号的密码（参见 code review C2）。
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=6)

    def validate(self, attrs):
        user = self.context['request'].user
        if not user or not user.is_authenticated:
            raise serializers.ValidationError('请先登录')
        if not user.check_password(attrs['old_password']):
            raise serializers.ValidationError('原密码错误')
        attrs['user'] = user
        return attrs


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6, min_length=6)
    password = serializers.CharField(write_only=True, min_length=6)

    def validate_email(self, value):
        if not value.endswith('@glazero.com'):
            raise serializers.ValidationError('仅允许 @glazero.com 邮箱')
        return value


class AdminCreateUserSerializer(serializers.ModelSerializer):
    """H5 fix: 管理员创建用户接口不允许直接授予 admin 角色；
    真正的 admin 角色提升只能通过数据库 / Django admin / 内部运维脚本。
    """
    password = serializers.CharField(write_only=True, min_length=6)
    role = serializers.ChoiceField(
        choices=[c for c in UserProfile.ROLE_CHOICES if c[0] != 'admin'],
        default='tester',
    )
    email = serializers.EmailField(required=True)
    username = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'role']

    def validate_email(self, value):
        if not value.endswith('@glazero.com'):
            raise serializers.ValidationError('仅允许 @glazero.com 邮箱')
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('该邮箱已被注册')
        return value

    def validate_role(self, value):
        # 二次防御：即使 meta 走了 choices 过滤，仍显式拒绝
        if value == 'admin':
            raise serializers.ValidationError('不能通过此接口创建管理员账号')
        return value

    def create(self, validated_data):
        role = validated_data.pop('role')
        username = validated_data.get('username', '')
        if not username:
            username = validated_data['email'].split('@')[0]
        validated_data['username'] = username
        user = User.objects.create_user(**validated_data)
        profile = UserProfile(user=user, role=role)
        apply_role_default_permissions(profile, role)
        profile.save()
        return user


class RegisterSerializer(serializers.ModelSerializer):
    # SECURITY: 公共注册不接受 role 字段；角色只能由管理员在后台分配，
    # 避免 self-service 越权获得 admin/developer（参见 code review C1）。
    password = serializers.CharField(write_only=True, min_length=6)
    email = serializers.EmailField(required=True)
    username = serializers.CharField(required=False, allow_blank=True)
    DEFAULT_ROLE = 'tester'

    class Meta:
        model = User
        fields = ['username', 'password', 'email']

    def validate_email(self, value):
        if not value.endswith('@glazero.com'):
            raise serializers.ValidationError('仅允许 @glazero.com 邮箱注册')
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('该邮箱已被注册')
        return value

    def create(self, validated_data):
        role = self.DEFAULT_ROLE
        username = validated_data.get('username', '')
        if not username:
            username = validated_data['email'].split('@')[0]
        validated_data['username'] = username
        user = User.objects.create_user(**validated_data)
        profile = UserProfile(user=user, role=role)
        apply_role_default_permissions(profile, role)
        profile.save()
        return user
