from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from apps.accounts.permissions import is_admin, user_can_access_projects
from .models import Defect
from .serializers import DefectListSerializer, DefectDetailSerializer


def _accessible_project_ids(user):
    """返回用户能访问的项目 id 列表。
    - admin / 有项目管理权限的用户：None（不限）
    - 其他：仅作为 ProjectMember 的项目
    """
    if is_admin(user) or user_can_access_projects(user):
        return None
    from apps.projects.models import Project
    return list(Project.objects.filter(members__user=user).values_list('id', flat=True))


class DefectViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Defect.objects.select_related('project', 'created_by', 'assigned_to', 'test_result')
        # SECURITY: 非管理类用户只能看到自己有成员关系的项目下的缺陷（C4）
        scoped = _accessible_project_ids(self.request.user)
        if scoped is not None:
            qs = qs.filter(project_id__in=scoped)
        project_id = self.request.query_params.get('project')
        status_filter = self.request.query_params.get('status')
        severity = self.request.query_params.get('severity')
        if project_id:
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
        serializer.save(created_by=self.request.user)
