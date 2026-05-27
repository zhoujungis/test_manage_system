from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Defect
from .serializers import DefectListSerializer, DefectDetailSerializer


class DefectViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Defect.objects.select_related('project', 'created_by', 'assigned_to').all()
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
