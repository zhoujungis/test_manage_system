import secrets
from django.db import transaction
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from .permissions import (
    IsNotTester,
    IsAdmin,
    is_admin,
    get_user_permissions,
    PERMISSION_FIELDS,
)
from .models import (
    UserProfile,
    apply_role_default_permissions,
    ROLE_DEFAULT_PERMISSIONS,
    VerificationCode,
    hash_verification_code,
)
from rest_framework.response import Response
from .serializers import (
    UserSerializer,
    RegisterSerializer,
    ChangePasswordSerializer,
    ResetPasswordSerializer,
)
from .throttles import (
    SendCodeRateThrottle,
    SendResetCodeRateThrottle,
    ChangePasswordRateThrottle,
    VerifyCodeRateThrottle,
)
from rest_framework.throttling import AnonRateThrottle
from .email_utils import send_mail_async

# C9 fix: 验证码 TTL 单一来源改为 VerificationCode.CODE_TTL_SECONDS，
# 避免 models 与 views 各写一份导致漂移。
CODE_TTL_SECONDS = VerificationCode.CODE_TTL_SECONDS

# 通用错误信息（不能用 page-level error 字符串，否则泄漏 email 是否已注册）
_GENERIC_VERIFY_FAIL = '验证码错误或已过期，或该邮箱未注册'


def _validate_glazero_email(email):
    return email.endswith('@glazero.com')


def _issue_verification_code(email, purpose, subject, message_tpl):
    """生成新的验证码；同一 email + purpose 旧的未消费码全部作废。"""
    code = VerificationCode.issue(email, purpose)
    send_mail_async(
        subject=subject,
        message=message_tpl.format(code=code),
        recipient_list=[email],
    )
    return code


def _verify_code(email, code, purpose):
    """返回：成功时返回 VerificationCode 实例；失败或锁定时返回 None。

    失败累计 attempts，attempts 达到 MAX_ATTEMPTS 即视为锁定；锁定后任何
    验证尝试都直接拒绝。
    """
    from django.utils import timezone
    target_hash = hash_verification_code(code)
    # 取最新一条同 email + purpose 的有效记录用于比较 / 计数
    with transaction.atomic():
        vc = (VerificationCode.objects
              .select_for_update()
              .filter(
                  email=email, purpose=purpose,
                  consumed_at__isnull=True,
              )
              .order_by('-created_at')
              .first())
        if not vc:
            return None
        if vc.is_locked:
            return None
        if (timezone.now() - vc.created_at).total_seconds() > CODE_TTL_SECONDS:
            return None
        # 用 compare_digest 减轻时序侧信道
        if not secrets.compare_digest(target_hash, vc.code_hash):
            vc.record_failure()
            return None
        # 标记消费
        vc.consumed_at = timezone.now()
        vc.save(update_fields=['consumed_at'])
        return vc


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle, SendCodeRateThrottle])
def send_code(request):
    email = request.data.get('email', '').strip()
    if not _validate_glazero_email(email):
        return Response({'error': '仅允许 @glazero.com 邮箱注册'}, status=status.HTTP_400_BAD_REQUEST)

    _issue_verification_code(
        email,
        VerificationCode.PURPOSE_REGISTER,
        '测试管理系统 - 注册验证码',
        '您的注册验证码是：{code}，5分钟内有效。',
    )
    return Response({'message': '验证码已发送'})


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle, SendResetCodeRateThrottle])
def send_reset_code(request):
    email = request.data.get('email', '').strip()
    if not _validate_glazero_email(email):
        return Response({'error': '仅允许 @glazero.com 邮箱'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email=email).exists():
        _issue_verification_code(
            email,
            VerificationCode.PURPOSE_RESET,
            '测试管理系统 - 重置密码验证码',
            '您正在重置密码，验证码是：{code}，5分钟内有效。如非本人操作请忽略。',
        )
    return Response({'message': '若该邮箱已注册，验证码将发送至您的邮箱'})


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([VerifyCodeRateThrottle])
def register(request):
    email = request.data.get('email', '').strip()
    code = request.data.get('code', '').strip()

    vc = _verify_code(email, code, VerificationCode.PURPOSE_REGISTER)
    if not vc:
        return Response({'error': _GENERIC_VERIFY_FAIL}, status=status.HTTP_400_BAD_REQUEST)

    serializer = RegisterSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        serializer.save()
    return Response({'message': '注册成功'}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([VerifyCodeRateThrottle])
def reset_password(request):
    email = request.data.get('email', '').strip()
    code = request.data.get('code', '').strip()

    serializer = ResetPasswordSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # SECURITY (C2/原 review): 不再用 '该邮箱未注册' 的分支消息，避免枚举；
    # 把 user lookup 放到验证成功之后，确保无法通过状态码 / 错误信息探测注册状态。
    vc = _verify_code(email, code, VerificationCode.PURPOSE_RESET)
    if not vc:
        return Response({'error': _GENERIC_VERIFY_FAIL}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.filter(email=email).first()
    if not user:
        # 理论上：邮箱已注册才会发出 reset code；到这里仍为 None 视为
        # 并发删除/异常。仍然返回通用错误，不暴露更多。
        return Response({'error': _GENERIC_VERIFY_FAIL}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        user.set_password(serializer.validated_data['password'])
        user.save()
        # 撤销该用户所有 outstanding refresh token
        from rest_framework_simplejwt.token_blacklist.models import (
            OutstandingToken, BlacklistedToken,
        )
        for t in OutstandingToken.objects.filter(user=user):
            BlacklistedToken.objects.get_or_create(token=t)
    return Response({'message': '密码已重置，请使用新密码登录'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([ChangePasswordRateThrottle])
def change_password(request):
    """改密：必须已登录，从 request.user 派生用户，不接受 body 里的 email/uid。
    修改成功后撤销所有 outstanding refresh token，强制重新登录。"""
    from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
    serializer = ChangePasswordSerializer(
        data=request.data,
        context={'request': request},
    )
    if not serializer.is_valid():
        err = serializer.errors
        if 'non_field_errors' in err:
            return Response({'error': err['non_field_errors'][0]}, status=status.HTTP_400_BAD_REQUEST)
        return Response(err, status=status.HTTP_400_BAD_REQUEST)

    user = serializer.validated_data['user']
    new_password = serializer.validated_data['new_password']
    user.set_password(new_password)
    with transaction.atomic():
        user.save()
        # 撤销该用户的所有有效 refresh token，强制所有已登录会话重新登录
        outstanding = OutstandingToken.objects.filter(user=user)
        for token in outstanding:
            BlacklistedToken.objects.get_or_create(token=token)
    return Response({'message': '密码修改成功，请使用新密码重新登录'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    user = User.objects.select_related('profile').filter(pk=request.user.pk).first()
    serializer = UserSerializer(user or request.user)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsNotTester])
def user_list(request):
    qs = User.objects.select_related('profile').all()
    serializer = UserSerializer(qs, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_user_permissions(request):
    """管理员：列出所有非管理员用户及权限配置。"""
    qs = User.objects.select_related('profile').filter(
        models.Q(profile__isnull=True) | ~models.Q(profile__role='admin')
    ).order_by('username')

    role_choices = [
        {'value': code, 'label': label}
        for code, label in UserProfile.ROLE_CHOICES
        if code != 'admin'
    ]
    permission_meta = [
        {'key': 'can_access_projects', 'label': '项目管理', 'desc': '访问项目管理模块及配置'},
        {'key': 'can_access_testcase_library', 'label': '测试用例库', 'desc': '查看产品线用例库'},
        {'key': 'can_manage_testcase_library', 'label': '管理用例库', 'desc': '新建、编辑、删除用例库用例'},
        {'key': 'can_access_my_projects', 'label': '我的项目', 'desc': '查看参与项目并执行分配用例'},
    ]
    users = UserSerializer(qs, many=True).data
    admins = UserSerializer(
        User.objects.select_related('profile').filter(profile__role='admin').order_by('username'),
        many=True,
    ).data
    return Response({
        'users': users,
        'admins': admins,
        'role_choices': role_choices,
        'permission_meta': permission_meta,
        'role_defaults': {
            role: defaults for role, defaults in ROLE_DEFAULT_PERMISSIONS.items() if role != 'admin'
        },
    })


@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_update_user_permissions(request, user_id):
    """管理员：更新指定非管理员用户的角色与权限。

    C7 fix: 用 select_for_update 包住「读 profile.role → 写回」全过程。
    否则两个管理员并发改同一个非管理员：A 检查时是 tester，B 中途把它升为 admin
    并 commit，A 的写仍会落到 admin 行上 → 越权。
    """
    from .serializers import AdminUserPermissionSerializer

    target = User.objects.filter(pk=user_id).first()
    if not target:
        return Response({'error': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)

    serializer = AdminUserPermissionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        # 行锁 profile（user_id 上有 OneToOneField 的 unique 索引）
        profile = (UserProfile.objects
                   .select_for_update()
                   .filter(user=target)
                   .first())
        if profile is None:
            # 不在事务里 get_or_create 会绕过锁；这里显式 create 后再加锁
            profile = UserProfile.objects.create(user=target, role='tester')
            profile = UserProfile.objects.select_for_update().get(pk=profile.pk)

        if profile.role == 'admin':
            return Response({'error': '不能修改管理员账号权限'}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        old_role = profile.role
        if data.get('apply_role_defaults') and 'role' in data:
            profile.role = data['role']
            apply_role_default_permissions(profile, profile.role)
        elif 'role' in data and data['role'] != old_role:
            profile.role = data['role']
            apply_role_default_permissions(profile, profile.role)
        elif 'role' in data:
            profile.role = data['role']

        for field in PERMISSION_FIELDS:
            if field in data:
                setattr(profile, field, data[field])

        profile.save()

    return Response(UserSerializer(target).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_create_user(request):
    """管理员：直接创建用户（无需验证码）。"""
    import logging
    from .serializers import AdminCreateUserSerializer
    audit = logging.getLogger('accounts.audit')

    serializer = AdminCreateUserSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    user = serializer.save()
    # H5 fix: 审计 —— 谁创建了谁，role 是什么。
    # 注意：serializer 已确保 role != 'admin'，但仍然留下日志以便复查。
    audit.info(
        'admin_create_user: actor=%s target=%s email=%s role=%s',
        getattr(request.user, 'username', '?'),
        user.username,
        user.email,
        getattr(user.profile, 'role', '?'),
    )
    return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_delete_user(request, user_id):
    """管理员：删除非管理员用户（不可删除自己）。"""
    if request.user.pk == user_id:
        return Response({'error': '不能删除当前登录账号'}, status=status.HTTP_400_BAD_REQUEST)

    target = User.objects.select_related('profile').filter(pk=user_id).first()
    if not target:
        return Response({'error': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)

    profile = UserProfile.objects.filter(user=target).first()
    if profile and profile.role == 'admin':
        return Response({'error': '不能删除管理员账号'}, status=status.HTTP_400_BAD_REQUEST)

    username = target.username
    with transaction.atomic():
        target.delete()
    return Response({'message': f'用户 {username} 已删除'})
