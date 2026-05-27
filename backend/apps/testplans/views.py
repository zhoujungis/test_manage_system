from django.db.models import Count
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import TestPlan, TestPlanCase
from .serializers import TestPlanListSerializer, TestPlanDetailSerializer


class TestPlanViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = TestPlan.objects.select_related('created_by').annotate(
            case_count=Count('plan_cases'),
        ).all()
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
        max_order = test_plan.plan_cases.count()
        for i, case_id in enumerate(case_ids):
            TestPlanCase.objects.get_or_create(
                test_plan=test_plan,
                test_case_id=case_id,
                defaults={'order': max_order + i + 1}
            )
        return Response({'message': '添加成功', 'count': len(case_ids)})

    @action(detail=True, methods=['delete'])
    def remove_case(self, request, pk=None):
        test_plan = self.get_object()
        case_id = request.data.get('case_id')
        if case_id:
            TestPlanCase.objects.filter(test_plan=test_plan, test_case_id=case_id).delete()
        return Response({'message': '移除成功'})
