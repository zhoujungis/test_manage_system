from rest_framework.permissions import BasePermission
from .models import UserProfile, ROLE_DEFAULT_PERMISSIONS, apply_role_default_permissions


PERMISSION_FIELDS = (
    'can_access_projects',
    'can_access_testcase_library',
    'can_manage_testcase_library',
    'can_access_my_projects',
)


def get_user_profile(user):
    if not user or not user.is_authenticated:
        return None
    profile, _ = UserProfile.objects.get_or_create(user=user, defaults={'role': 'tester'})
    return profile


def get_user_role(user):
    profile = get_user_profile(user)
    return profile.role if profile else None


def is_admin(user):
    return get_user_role(user) == 'admin'


def is_viewer(user):
    return get_user_role(user) == 'viewer'


def get_user_permissions(user):
    profile = get_user_profile(user)
    if not profile:
        return {k: False for k in PERMISSION_FIELDS}
    if is_admin(user):
        return {k: True for k in PERMISSION_FIELDS}
    perms = {field: getattr(profile, field) for field in PERMISSION_FIELDS}
    if profile.role == 'viewer':
        read_keys = (
            'can_access_projects',
            'can_access_testcase_library',
            'can_access_my_projects',
        )
        if not any(perms[k] for k in read_keys):
            perms.update(ROLE_DEFAULT_PERMISSIONS['viewer'])
    return perms


def user_can_write_projects(user):
    return user_can_access_projects(user) and not is_viewer(user)


def user_can_access_projects(user):
    if is_admin(user):
        return True
    profile = get_user_profile(user)
    return profile.can_access_projects if profile else False


def user_can_access_testcase_library(user):
    if is_admin(user):
        return True
    profile = get_user_profile(user)
    return profile.can_access_testcase_library if profile else False


def user_can_manage_testcase_library(user):
    if is_admin(user):
        return True
    profile = get_user_profile(user)
    return profile.can_manage_testcase_library if profile else False


def user_can_access_my_projects(user):
    if is_admin(user):
        return True
    profile = get_user_profile(user)
    return profile.can_access_my_projects if profile else False


# 兼容旧逻辑
def is_tester(user):
    return get_user_role(user) == 'tester'


class IsAdmin(BasePermission):
    message = '仅管理员可执行此操作'

    def has_permission(self, request, view):
        return request.user.is_authenticated and is_admin(request.user)


class IsNotTester(BasePermission):
    """项目管理：读操作需有项目管理权限；写操作观察者不可用。"""

    message = '无权访问项目管理'

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return user_can_access_projects(request.user)
        return user_can_write_projects(request.user)


class ProjectMemberReadPermission(BasePermission):
    """项目内资源（tasks/members/modules）：允许项目成员或用例库管理者读取。"""

    message = '无权访问该项目资源'

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            if user_can_access_projects(request.user) or user_can_access_my_projects(request.user):
                return True
            return False
        return user_can_write_projects(request.user)

    def has_object_permission(self, request, view, obj):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            if user_can_access_projects(request.user):
                return True
            # 用例库管理者可以查看任意项目的模块，方便关联用例
            if user_can_manage_testcase_library(request.user):
                return True
        else:
            if user_can_access_projects(request.user):
                if is_viewer(request.user):
                    return False
                return True
            return False

        from apps.projects.models import ProjectMember
        is_member = ProjectMember.objects.filter(project=obj, user=request.user).exists()
        if not is_member:
            return False
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return user_can_access_my_projects(request.user)
        return False


class ProjectPermission(BasePermission):
    """项目 API：按权限与成员关系控制。"""

    message = '无权访问该项目'

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if user_can_access_projects(request.user):
            if is_viewer(request.user):
                if view.action in ('list', 'retrieve'):
                    return True
                if view.action == 'case_assignments' and request.method in ('GET', 'HEAD', 'OPTIONS'):
                    return True
                return False
            return True
        allowed = {'list', 'retrieve', 'case_assignments'}
        return view.action in allowed

    def has_object_permission(self, request, view, obj):
        if user_can_access_projects(request.user):
            if is_viewer(request.user):
                return view.action in ('retrieve', 'case_assignments')
            return True
        from apps.projects.models import ProjectMember
        is_member = ProjectMember.objects.filter(project=obj, user=request.user).exists()
        if view.action in ('retrieve', 'case_assignments'):
            return is_member and user_can_access_my_projects(request.user)
        return False


class TestCaseAssignmentPermission(BasePermission):
    message = '无权操作该测试分配'

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if not user_can_access_my_projects(request.user):
            return False
        if user_can_access_projects(request.user):
            if is_viewer(request.user):
                return view.action == 'retrieve'
            return True
        return view.action in ('retrieve', 'update', 'partial_update')

    def has_object_permission(self, request, view, obj):
        if user_can_access_projects(request.user):
            if is_viewer(request.user):
                return view.action == 'retrieve'
            return True
        return obj.assigned_to_id == request.user.id


class ModulePermission(BasePermission):
    """模块管理：项目管理者或用例库管理者可操作，删除仅限项目管理者。"""

    message = '无权管理模块'

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            if user_can_access_projects(request.user) or user_can_manage_testcase_library(request.user):
                return True
            return False
        if request.method == 'DELETE':
            return user_can_write_projects(request.user)
        return user_can_write_projects(request.user) or user_can_manage_testcase_library(request.user)


class TestCaseLibraryPermission(BasePermission):
    message = '无权访问测试用例库'

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if not user_can_access_testcase_library(request.user):
            return False
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        if request.method == 'DELETE':
            return user_can_write_projects(request.user) or is_admin(request.user)
        return user_can_manage_testcase_library(request.user)
