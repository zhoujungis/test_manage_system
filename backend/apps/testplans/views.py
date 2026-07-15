from django.db.models import Count
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.accounts.permissions import is_admin, user_can_access_projects
from .models import TestPlan, TestPlanCase
from .serializers import TestPlanListSerializer, TestPlanDetailSerializer


def _accessible_project_ids(user):
    """返回用户能访问的项目 id 列表。
    - admin / 有项目管理权限的用户：None（不限）
    - 其他：仅作为 ProjectMember 的项目
    """
    if is_admin(user) or user_can_access_projects(user):
        return None
    from apps.projects.models import Project
    return list(Project.objects.filter(members__user=user).values_list('id', flat=True))


class TestPlanViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = TestPlan.objects.select_related('created_by', 'project').annotate(
            case_count=Count('plan_cases'),
        )
        # SECURITY: 非管理类用户只能看到自己有成员关系的项目下的计划（C4）
        scoped = _accessible_project_ids(self.request.user)
        if scoped is not None:
            qs = qs.filter(project_id__in=scoped)
        project_id = self.request.query_params.get('project')
        if project_id:
            qs = qs.filter(project_id=project_id)
        return qs

    def get_serializer_class(self):
        if self.action in ['retrieve', 'create', 'update', 'partial_update']:
            return TestPlanDetailSerializer
        return TestPlanListSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def add_cases(self, request, pk=None):
        test_plan = self.get_object()
        case_ids = request.data.get('case_ids', [])
        # 仅允许加当前计划所在项目下的用例（防跨项目污染）
        plan_project_test_cases = set(
            test_plan.project.test_cases.values_list('id', flat=True)
        ) if test_plan.project else set()
        filtered_case_ids = [cid for cid in case_ids if cid in plan_project_test_cases]
        max_order = test_plan.plan_cases.count()
        for i, case_id in enumerate(filtered_case_ids):
            TestPlanCase.objects.get_or_create(
                test_plan=test_plan,
                test_case_id=case_id,
                defaults={'order': max_order + i + 1}
            )
        return Response({'message': '添加成功', 'count': len(filtered_case_ids)})

    @action(detail=True, methods=['delete'])
    def remove_case(self, request, pk=None):
        test_plan = self.get_object()
        case_id = request.data.get('case_id')
        if case_id:
            TestPlanCase.objects.filter(test_plan=test_plan, test_case_id=case_id).delete()
        return Response({'message': '移除成功'})
