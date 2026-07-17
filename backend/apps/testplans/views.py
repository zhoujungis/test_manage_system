from django.db.models import Count
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.accounts.permissions import accessible_project_ids
from .models import TestPlan, TestPlanCase
from .serializers import TestPlanListSerializer, TestPlanDetailSerializer


class TestPlanViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = TestPlan.objects.select_related('created_by', 'project').annotate(
            case_count=Count('plan_cases'),
        )
        # SECURITY: 非管理类用户只能看到自己有成员关系的项目下的计划（C4）
        scoped = accessible_project_ids(self.request.user)
        if scoped is not None:
            qs = qs.filter(project_id__in=scoped)
        project_id = self.request.query_params.get('project')
        if project_id:
            # C2 fix: ?project= 必须落在 scope 内，做交集防止 IDOR
            if scoped is not None:
                qs = qs.filter(project_id=project_id, project_id__in=scoped)
            else:
                qs = qs.filter(project_id=project_id)
        return qs

    def get_serializer_class(self):
        if self.action in ['retrieve', 'create', 'update', 'partial_update']:
            return TestPlanDetailSerializer
        return TestPlanListSerializer

    def perform_create(self, serializer):
        # C3 fix: 校验 plan.project 在用户的 accessible scope 内
        # 否则任何登录用户都可 POST {project: <任意项目>} 创建跨项目计划
        from rest_framework.exceptions import PermissionDenied
        project = serializer.validated_data.get('project')
        if project is not None:
            scoped = accessible_project_ids(self.request.user)
            if scoped is not None and project.id not in scoped:
                raise PermissionDenied('无权在该项目下创建测试计划')
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        # 同样校验 update 不允许把 plan 移到越权的 project
        from rest_framework.exceptions import PermissionDenied
        project = serializer.validated_data.get('project', serializer.instance.project)
        if project is not None:
            scoped = accessible_project_ids(self.request.user)
            if scoped is not None and project.id not in scoped:
                raise PermissionDenied('无权把该测试计划移到此项目')
        serializer.save()

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
