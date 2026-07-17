from django.db import transaction
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.accounts.permissions import TestCaseLibraryPermission, accessible_project_ids
from .models import TestCase
from .serializers import TestCaseListSerializer, TestCaseDetailSerializer


class AllOrPagedPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

    def paginate_queryset(self, queryset, request, view=None):
        if request.query_params.get('all') == '1':
            return None
        return super().paginate_queryset(queryset, request, view)


def _parse_int_query_param(request, name):
    """H8 fix: 把 ?project=abc 这种垃圾输入转 400 而不是 ValueError 500。
    返回 (int|None, None) 或 (None, Response(400))。
    """
    raw = request.query_params.get(name)
    if raw is None or raw == '':
        return None, None
    try:
        return int(raw), None
    except (TypeError, ValueError):
        return None, Response({name: f'必须是整数'}, status=400)


class TestCaseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, TestCaseLibraryPermission]
    pagination_class = AllOrPagedPagination

    def get_queryset(self):
        qs = TestCase.objects.select_related('project', 'module', 'created_by', 'updated_by').all()
        # H15 fix: 非管理员按项目成员关系 scope，避免有 library 权限的 tester 看任意项目用例
        scoped = accessible_project_ids(self.request.user)
        if scoped is not None:
            qs = qs.filter(project_id__in=scoped)
        project_id, err = _parse_int_query_param(self.request, 'project')
        if err: raise ValidationError({'project': '必须是整数'})
        module_id, err = _parse_int_query_param(self.request, 'module')
        if err: raise ValidationError({'module': '必须是整数'})
        status_filter = self.request.query_params.get('status')
        priority = self.request.query_params.get('priority')
        type_filter = self.request.query_params.get('type')
        product_line = self.request.query_params.get('product_line')
        search = self.request.query_params.get('search')
        if project_id:
            qs = qs.filter(project_id=project_id)
        if module_id:
            qs = qs.filter(module_id=module_id)
        if status_filter:
            qs = qs.filter(status=status_filter)
        if priority:
            qs = qs.filter(priority=priority)
        if type_filter:
            qs = qs.filter(case_type=type_filter)  # 字段名迁移 type→case_type (M4 fix)
        if product_line:
            qs = qs.filter(product_line=product_line)
        if search:
            qs = qs.filter(title__icontains=search)
        return qs

    def get_serializer_class(self):
        if self.action in ['retrieve', 'create', 'update', 'partial_update']:
            return TestCaseDetailSerializer
        return TestCaseListSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


@api_view(['GET'])
@permission_classes([IsAuthenticated, TestCaseLibraryPermission])
def testcase_tree(request):
    """用例库树视图专用端点：返回每条用例的最小投影（id/title/priority/module_name），
    不返回 description / preconditions / steps / created_by 等重型字段。

    用于左侧 el-tree，避免一次拉整库（2000+ 用例时旧 all=1 路径会卡前端）。

    Query:
      - product_line (required)
      - priority, type, status (optional filter)
      - limit (default 500, hard max 2000)

    响应：{count, results: [{id, title, priority, type, status, module_id, module_name}, ...]}
    """
    product_line = request.query_params.get('product_line')
    if not product_line:
        return Response({'error': 'product_line is required'}, status=400)

    qs = TestCase.objects.select_related('module').filter(product_line=product_line)
    # query param 名 (API 契约) ≠ 模型字段名：M4 fix 后字段是 case_type
    for param, field in (('priority', 'priority'), ('type', 'case_type'), ('status', 'status')):
        v = request.query_params.get(param)
        if v:
            qs = qs.filter(**{field: v})

    try:
        limit = min(int(request.query_params.get('limit', '500')), 2000)
    except (TypeError, ValueError):
        return Response({'error': 'limit 必须是整数'}, status=400)

    qs = qs.order_by('-created_at')[:limit]
    data = [
        {
            'id': tc.id,
            'title': tc.title,
            'priority': tc.priority,
            'type': tc.case_type,  # 模型字段 case_type，JSON 键保持 'type'（API 契约）
            'status': tc.status,
            'module_id': tc.module_id,
            'module_name': tc.module.name if tc.module else None,
        }
        for tc in qs
    ]
    return Response({'count': len(data), 'results': data})
