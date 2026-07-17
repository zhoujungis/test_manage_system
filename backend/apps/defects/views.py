from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from apps.accounts.permissions import accessible_project_ids
from .models import Defect
from .serializers import DefectListSerializer, DefectDetailSerializer


class DefectViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Defect.objects.select_related('project', 'created_by', 'assigned_to', 'test_result')
        # SECURITY: 非管理类用户只能看到自己有成员关系的项目下的缺陷（C4）
        scoped = accessible_project_ids(self.request.user)
        if scoped is not None:
            qs = qs.filter(project_id__in=scoped)
        project_id = self.request.query_params.get('project')
        status_filter = self.request.query_params.get('status')
        severity = self.request.query_params.get('severity')
        if project_id:
            # C2 fix: ?project= 必须落在 scope 内，做交集防止 IDOR
            # （之前 qs.filter(project_id=project_id) 会覆盖 scope 过滤）
            if scoped is not None:
                qs = qs.filter(project_id=project_id, project_id__in=scoped)
            else:
                qs = qs.filter(project_id=project_id)
        if status_filter:
            qs = qs.filter(status=status_filter)
        if severity:
            qs = qs.filter(severity=severity)
        return qs

    def get_serializer_class(self):
        if self.action in ['retrieve', 'create', 'update', 'partial_update']:
            return DefectDetailSerializer
        return DefectListSerializer

    def perform_create(self, serializer):
        # C3 fix: defect.project 必须在用户的 accessible scope 内
        from rest_framework.exceptions import PermissionDenied
        project = serializer.validated_data.get('project')
        if project is not None:
            scoped = accessible_project_ids(self.request.user)
            if scoped is not None and project.id not in scoped:
                raise PermissionDenied('无权在该项目下创建缺陷')
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        from rest_framework.exceptions import PermissionDenied
        project = serializer.validated_data.get('project', serializer.instance.project)
        if project is not None:
            scoped = accessible_project_ids(self.request.user)
            if scoped is not None and project.id not in scoped:
                raise PermissionDenied('无权把缺陷移到此项目')
        serializer.save()
