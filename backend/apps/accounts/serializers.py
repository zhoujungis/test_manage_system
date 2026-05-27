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
        email = attrs.get('email', '')
        password = attrs.get('password', '')

        user = User.objects.filter(email=email).first()
        if not user or not user.is_active:
            raise serializers.ValidationError('邮箱或密码错误')

        authenticated = authenticate(
            request=self.context.get('request'),
            username=user.username,
            password=password,
        )
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

    def _get_profile(self, user):
        profile, _ = UserProfile.objects.get_or_create(user=user, defaults={'role': 'tester'})
        return profile

    def get_profile(self, user):
        return UserProfileSerializer(self._get_profile(user)).data

    def get_role(self, user):
        return self._get_profile(user).role

    def get_role_label(self, user):
        return self._get_profile(user).get_role_display()

    def get_phone(self, user):
        return self._get_profile(user).phone or ''

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
    email = serializers.EmailField()
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=6)

    def validate_email(self, value):
        if not value.endswith('@glazero.com'):
            raise serializers.ValidationError('仅允许 @glazero.com 邮箱')
        return value

    def validate(self, attrs):
        user = User.objects.filter(email=attrs['email']).first()
        if not user or not user.check_password(attrs['old_password']):
            raise serializers.ValidationError('邮箱或原密码错误')
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
    password = serializers.CharField(write_only=True, min_length=6)
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, default='tester')
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
    password = serializers.CharField(write_only=True, min_length=6)
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, default='tester')
    email = serializers.EmailField(required=True)
    username = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'role']

    def validate_email(self, value):
        if not value.endswith('@glazero.com'):
            raise serializers.ValidationError('仅允许 @glazero.com 邮箱注册')
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('该邮箱已被注册')
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
