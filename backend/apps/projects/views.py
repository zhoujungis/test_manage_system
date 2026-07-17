from django.db import transaction
from django.db.models import Count
from django.core.cache import cache
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.accounts.permissions import (
    IsNotTester,
    ModulePermission,
    ProjectPermission,
    ProjectMemberReadPermission,
    TestCaseAssignmentPermission,
    user_can_access_projects,
    user_can_access_my_projects,
    user_can_manage_testcase_library,
    user_can_write_projects,
)
from django.conf import settings
from .models import Project, Module, ProjectMember, ProjectTask, TestCaseAssignment, AssignmentAttachment
from .serializers import (
    ProjectSerializer, ModuleSerializer, ProjectMemberSerializer,
    ProjectTaskSerializer, TestCaseAssignmentSerializer,
    TestCaseAssignmentTreeSerializer, AssignmentAttachmentSerializer,
)


class _ActionPagination(PageNumberPagination):
    """H4 fix: 自定义 @action 默认返回不带分页；这个 paginator 给嵌套端点用。"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 200

    def _paginate(self, qs, request, view=None):
        # 若调用方传 ?all=1 则不分页（保持向后兼容）
        if request.query_params.get('all') == '1':
            return list(qs), None
        self.request = request
        page = self.paginate_queryset(qs, request, view=view)
        return page, self


def paginated_response(qs, serializer_class, request, view=None):
    """H4 fix helper: 序列化 + 分页，返回带 count/next/previous/results 的标准响应。
    自定义 @action 直接 return Response(serializer.data) 会绕过全局分页器。
    """
    paginator = _ActionPagination()
    page = paginator.paginate_queryset(qs, request, view=view)
    if page is not None:
        serializer = serializer_class(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    # 不分页路径（all=1 或空 queryset）
    serializer = serializer_class(qs, many=True)
    return Response({'count': qs.count() if hasattr(qs, 'count') else len(qs),
                     'next': None, 'previous': None, 'results': serializer.data})


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.select_related('created_by').all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, ProjectPermission]

    def get_queryset(self):
        qs = super().get_queryset().annotate(
            module_count=Count('modules', distinct=True),
            testcase_count=Count('testcases', distinct=True),
            testplan_count=Count('testplans', distinct=True),
            member_count=Count('members', distinct=True),
            task_count=Count('tasks', distinct=True),
        )
        if not user_can_access_projects(self.request.user):
            qs = qs.filter(members__user=self.request.user).distinct()
        else:
            if self.request.query_params.get('my') == '1':
                qs = qs.filter(members__user=self.request.user)
            if self.request.query_params.get('led') == '1':
                qs = qs.filter(created_by=self.request.user)
        return qs

    def perform_create(self, serializer):
        project = serializer.save(created_by=self.request.user)
        ProjectMember.objects.create(project=project, user=self.request.user, role='leader')

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated, ProjectMemberReadPermission])
    def modules(self, request, pk=None):
        project = self.get_object()
        # H4 fix: 模块列表走分页
        return paginated_response(project.modules.all(), ModuleSerializer, request, self)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def add_module(self, request, pk=None):
        project = self.get_object()
        if not (user_can_write_projects(request.user) or user_can_manage_testcase_library(request.user)):
            return Response({'detail': '无权添加模块'}, status=status.HTTP_403_FORBIDDEN)
        serializer = ModuleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(project=project)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get', 'post'], permission_classes=[IsAuthenticated, ProjectMemberReadPermission])
    def members(self, request, pk=None):
        project = self.get_object()
        if request.method == 'GET':
            # H4 fix: 成员列表走分页
            qs = project.members.select_related('user').all()
            return paginated_response(qs, ProjectMemberSerializer, request, self)
        serializer = ProjectMemberSerializer(data=request.data, context={'project': project})
        if serializer.is_valid():
            serializer.save(project=project)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get', 'post'], permission_classes=[IsAuthenticated, ProjectMemberReadPermission])
    def tasks(self, request, pk=None):
        project = self.get_object()
        if request.method == 'GET':
            # H4 fix: 任务列表走分页
            qs = project.tasks.select_related('assigned_to', 'created_by').all()
            return paginated_response(qs, ProjectTaskSerializer, request, self)
        serializer = ProjectTaskSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(project=project, created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsNotTester])
    def batch_approve(self, request, pk=None):
        project = self.get_object()
        ids = request.data.get('ids', [])
        with transaction.atomic():
            updated = project.case_assignments.select_for_update().filter(id__in=ids).exclude(status='pending').update(approval_status='approved')
        cache.delete(f'case_assignments_{project.id}')
        return Response({'updated': updated})

    @action(detail=True, methods=['get', 'post'])
    def case_assignments(self, request, pk=None):
        project = self.get_object()
        if request.method == 'GET':
            cache_key = f'case_assignments_{project.id}'
            # Only cache unfiltered list
            has_filters = any(request.query_params.get(k) for k in ['assigned_to', 'status', 'priority', 'approval_status', 'task_id'])
            if not has_filters:
                cached = cache.get(cache_key)
                if cached is not None:
                    return Response(cached)

            qs = project.case_assignments.select_related(
                'test_case__module', 'test_case__project', 'assigned_to', 'task'
            ).prefetch_related('attachments', 'attachments__uploaded_by').all()
            assigned_to = request.query_params.get('assigned_to')
            if assigned_to == 'me':
                qs = qs.filter(assigned_to=request.user)
            elif assigned_to:
                qs = qs.filter(assigned_to_id=assigned_to)
            status_filter = request.query_params.get('status')
            if status_filter:
                qs = qs.filter(status__in=status_filter.split(','))
            priority_filter = request.query_params.get('priority')
            if priority_filter:
                qs = qs.filter(test_case__priority__in=priority_filter.split(','))
            approval_filter = request.query_params.get('approval_status')
            if approval_filter:
                qs = qs.filter(approval_status__in=approval_filter.split(','))
            task_id = request.query_params.get('task_id')
            if task_id:
                qs = qs.filter(task_id=task_id)
            serializer = TestCaseAssignmentTreeSerializer(qs, many=True)
            data = serializer.data
            if not has_filters:
                cache.set(cache_key, data, 30)
            return Response(data)
        if not user_can_write_projects(request.user):
            return Response({'detail': '只读账号无权分配用例'}, status=status.HTTP_403_FORBIDDEN)
        # Support both single and batch create
        tc_ids = request.data.get('test_case_ids')
        if tc_ids:
            task_id = request.data.get('task_id')
            if task_id:
                try:
                    task = ProjectTask.objects.get(id=task_id, project=project)
                except ProjectTask.DoesNotExist:
                    return Response({'detail': '所选任务不存在或不属于当前项目'}, status=status.HTTP_400_BAD_REQUEST)
            created = 0
            updated = 0
            new_assignee = request.data.get('assigned_to')
            new_status = request.data.get('status', 'pending')
            new_notes = request.data.get('notes', '')
            with transaction.atomic():
                for tc_id in tc_ids:
                    existing = TestCaseAssignment.objects.select_for_update().filter(project=project, test_case_id=tc_id).first()
                    if existing:
                        existing.assigned_to_id = new_assignee
                        existing.status = new_status
                        existing.notes = new_notes
                        if task_id:
                            existing.task_id = task_id
                        existing.save()
                        updated += 1
                    else:
                        TestCaseAssignment.objects.create(
                            project=project, task_id=task_id, test_case_id=tc_id,
                            assigned_to_id=new_assignee,
                            status=new_status, notes=new_notes,
                            created_by=request.user,
                        )
                        created += 1
            cache.delete(f'case_assignments_{project.id}')
            return Response({'created': created, 'updated': updated}, status=status.HTTP_201_CREATED)
        serializer = TestCaseAssignmentSerializer(data=request.data, context={'project': project})
        if serializer.is_valid():
            serializer.save(project=project, created_by=request.user)
            cache.delete(f'case_assignments_{project.id}')
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ModuleViewSet(viewsets.ModelViewSet):
    queryset = Module.objects.select_related('project').annotate(
        case_count=Count('testcases'),
    )
    serializer_class = ModuleSerializer
    permission_classes = [IsAuthenticated, ModulePermission]


class ProjectMemberViewSet(viewsets.ModelViewSet):
    # C6 fix: 根路径 /project-members/ 不再有「任意 dev 改任意项目成员」的口子。
    # queryset 限定到用户能访问的项目；perform_create/perform_update 也校验。
    serializer_class = ProjectMemberSerializer
    permission_classes = [IsAuthenticated, IsNotTester]

    def get_queryset(self):
        qs = ProjectMember.objects.select_related('user', 'project').all()
        scoped = accessible_project_ids(self.request.user)
        if scoped is not None:
            qs = qs.filter(project_id__in=scoped)
        return qs

    def perform_create(self, serializer):
        project = serializer.validated_data.get('project')
        self._check_project_scope(project)
        serializer.save()

    def perform_update(self, serializer):
        project = serializer.instance.project
        self._check_project_scope(project)
        serializer.save()

    def _check_project_scope(self, project):
        if project is None:
            return  # 兜底交给 serializer 校验
        scoped = accessible_project_ids(self.request.user)
        if scoped is None:
            return  # admin / 有项目管理权限
        if project.id not in scoped:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('无权操作该项目的成员')


class ProjectTaskViewSet(viewsets.ModelViewSet):
    # C6 fix: 同 ProjectMember。
    serializer_class = ProjectTaskSerializer
    permission_classes = [IsAuthenticated, IsNotTester]

    def get_queryset(self):
        qs = ProjectTask.objects.select_related('assigned_to', 'created_by', 'project').all()
        scoped = accessible_project_ids(self.request.user)
        if scoped is not None:
            qs = qs.filter(project_id__in=scoped)
        return qs

    def perform_create(self, serializer):
        project = serializer.validated_data.get('project')
        self._check_project_scope(project)
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        project = serializer.instance.project
        self._check_project_scope(project)
        serializer.save()

    def _check_project_scope(self, project):
        if project is None:
            return
        scoped = accessible_project_ids(self.request.user)
        if scoped is None:
            return
        if project.id not in scoped:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('无权操作该项目的任务')


class TestCaseAssignmentViewSet(viewsets.ModelViewSet):
    queryset = TestCaseAssignment.objects.select_related(
        'test_case__module', 'test_case__project', 'assigned_to', 'project', 'task'
    ).prefetch_related('attachments', 'attachments__uploaded_by').all()
    serializer_class = TestCaseAssignmentSerializer
    permission_classes = [IsAuthenticated, TestCaseAssignmentPermission]

    def perform_create(self, serializer):
        instance = serializer.save(created_by=self.request.user)
        cache.delete(f'case_assignments_{instance.project_id}')

    def perform_update(self, serializer):
        instance = serializer.save()
        cache.delete(f'case_assignments_{instance.project_id}')

    def perform_destroy(self, instance):
        cache.delete(f'case_assignments_{instance.project_id}')
        instance.delete()

    def _can_manage_assignment(self, assignment, user):
        if user_can_write_projects(user):
            return True
        return assignment.assigned_to_id == user.id and user_can_access_my_projects(user)

    @action(detail=True, methods=['get', 'post'], url_path='attachments')
    def attachments(self, request, pk=None):
        assignment = self.get_object()
        if not self._can_manage_assignment(assignment, request.user):
            return Response({'detail': '无权操作该测试分配'}, status=status.HTTP_403_FORBIDDEN)

        if request.method == 'GET':
            qs = assignment.attachments.select_related('uploaded_by').all()
            # H4 fix: 附件列表走分页
            return paginated_response(qs, AssignmentAttachmentSerializer, request, self)

        upload = request.FILES.get('file')
        if not upload:
            return Response({'error': '请选择文件'}, status=status.HTTP_400_BAD_REQUEST)
        max_size = getattr(settings, 'ASSIGNMENT_ATTACHMENT_MAX_BYTES', 15 * 1024 * 1024)
        if upload.size > max_size:
            return Response({'error': '文件大小不能超过 15MB'}, status=status.HTTP_400_BAD_REQUEST)
        # H14 fix: 限制 MIME 和扩展名白名单；否则攻击者可传 .exe / .html / .svg 内嵌 JS
        _BLOCKED_EXT = {
            '.exe', '.bat', '.cmd', '.sh', '.ps1',
            '.html', '.htm', '.svg', '.js', '.jsx', '.ts', '.mjs',
            '.jar', '.war', '.php', '.py', '.rb',
            '.msi', '.scr', '.vbs', '.wsf',
        }
        import os
        _ext = os.path.splitext(upload.name)[1].lower()
        if _ext in _BLOCKED_EXT:
            return Response({'error': f'不允许上传 {_ext} 类型的文件'}, status=status.HTTP_400_BAD_REQUEST)
        _ALLOWED_MIMES_PREFIX = (
            'image/', 'text/', 'application/pdf', 'application/zip',
            'application/json', 'application/xml',
            'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument',
            'application/msword', 'application/octet-stream',  # 通用二进制
        )
        if not (upload.content_type or '').startswith(_ALLOWED_MIMES_PREFIX):
            return Response(
                {'error': f'不支持的 MIME 类型: {upload.content_type}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        att = AssignmentAttachment.objects.create(
            assignment=assignment,
            file=upload,
            original_name=upload.name,
            file_size=upload.size,
            uploaded_by=request.user,
        )
        cache.delete(f'case_assignments_{assignment.project_id}')
        serializer = AssignmentAttachmentSerializer(att, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path=r'attachments/(?P<attachment_id>[^/.]+)')
    def delete_attachment(self, request, pk=None, attachment_id=None):
        assignment = self.get_object()
        if not self._can_manage_assignment(assignment, request.user):
            return Response({'detail': '无权操作该测试分配'}, status=status.HTTP_403_FORBIDDEN)
        att = assignment.attachments.filter(pk=attachment_id).first()
        if not att:
            return Response({'error': '附件不存在'}, status=status.HTTP_404_NOT_FOUND)
        if att.file:
            att.file.delete(save=False)
        att.delete()
        cache.delete(f'case_assignments_{assignment.project_id}')
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def library_modules(request):
    """用例库模块：GET 按产品线列出全部模块，POST 新增模块。"""
    product_line = (request.query_params.get('product_line') or request.data.get('product_line') or '').strip()

    if request.method == 'GET':
        # H4 fix: 用例库模块列表走分页
        qs = Module.objects.filter(project__product_line=product_line).select_related('project')
        return paginated_response(qs, ModuleSerializer, request)

    if not (user_can_write_projects(request.user) or user_can_manage_testcase_library(request.user)):
        return Response({'detail': '无权添加模块'}, status=status.HTTP_403_FORBIDDEN)

    name = (request.data.get('name') or '').strip()
    if not name:
        return Response({'error': '模块名称不能为空'}, status=status.HTTP_400_BAD_REQUEST)

    # H16 fix: 不再静默 fallback 到 Project.objects.first() —— 那会让 product_line
    # 不匹配的模块挂到任意项目上，无审计。加一个明确 product_line 的项目必须存在。
    project = Project.objects.filter(product_line=product_line).first()
    if not project:
        return Response(
            {'error': f'当前产品线 {product_line} 下暂无项目，请先在该产品线下创建项目'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    module = Module.objects.create(project=project, name=name)
    serializer = ModuleSerializer(module)
    return Response(serializer.data, status=status.HTTP_201_CREATED)
