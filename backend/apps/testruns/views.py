from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.accounts.permissions import is_admin, user_can_access_projects
from .models import TestRun, TestResult
from .serializers import (TestRunListSerializer, TestRunDetailSerializer,
                          TestResultSerializer, TestResultUpdateSerializer)


def _accessible_project_ids(user):
    """返回用户能访问的项目 id 列表。
    - admin / 有项目管理权限的用户：None（不限）
    - 其他：仅作为 ProjectMember 的项目
    """
    if is_admin(user) or user_can_access_projects(user):
        return None
    from apps.projects.models import Project
    return list(Project.objects.filter(members__user=user).values_list('id', flat=True))


class TestRunViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = TestRun.objects.select_related('test_plan', 'test_plan__project', 'created_by').annotate(
            total=Count('results', distinct=True),
            passed=Count('results', filter=Q(results__status='pass'), distinct=True),
            failed=Count('results', filter=Q(results__status='fail'), distinct=True),
        )
        # SECURITY: 非管理类用户只能看到自己有成员关系的项目下的测试执行（C4）
        scoped = _accessible_project_ids(self.request.user)
        if scoped is not None:
            qs = qs.filter(test_plan__project_id__in=scoped)
        plan_id = self.request.query_params.get('plan')
        project_id = self.request.query_params.get('project')
        if plan_id:
            qs = qs.filter(test_plan_id=plan_id)
        if project_id:
            qs = qs.filter(test_plan__project_id=project_id)
        return qs

    def get_serializer_class(self):
        if self.action in ['retrieve', 'create', 'update', 'partial_update']:
            return TestRunDetailSerializer
        return TestRunListSerializer

    def perform_create(self, serializer):
        with transaction.atomic():
            test_run = serializer.save(created_by=self.request.user)
            plan_cases = test_run.test_plan.plan_cases.select_related('test_case').all()
            TestResult.objects.bulk_create([
                TestResult(test_run=test_run, test_case=pc.test_case)
                for pc in plan_cases
            ])

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        test_run = self.get_object()
        if test_run.status != 'pending':
            return Response({'error': '只能启动待执行的测试运行'}, status=status.HTTP_400_BAD_REQUEST)
        test_run.status = 'running'
        test_run.started_at = timezone.now()
        test_run.save()
        return Response({'message': '测试执行已开始'})

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        test_run = self.get_object()
        if test_run.status != 'running':
            return Response({'error': '只能完成正在执行中的测试运行'}, status=status.HTTP_400_BAD_REQUEST)
        test_run.status = 'completed'
        test_run.completed_at = timezone.now()
        test_run.save()
        return Response({'message': '测试执行已完成'})

    @action(detail=True, methods=['patch'])
    def update_result(self, request, pk=None):
        test_run = self.get_object()
        if test_run.status != 'running':
            return Response({'error': '只能更新执行中的测试结果'}, status=status.HTTP_400_BAD_REQUEST)
        result_id = request.data.get('result_id')
        try:
            result = test_run.results.get(id=result_id)
        except TestResult.DoesNotExist:
            return Response({'error': '结果不存在'}, status=status.HTTP_404_NOT_FOUND)
        serializer = TestResultUpdateSerializer(result, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(executed_by=request.user, executed_at=timezone.now())
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
