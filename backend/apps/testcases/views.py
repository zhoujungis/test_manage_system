from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from apps.accounts.permissions import TestCaseLibraryPermission
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


class TestCaseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, TestCaseLibraryPermission]
    pagination_class = AllOrPagedPagination

    def get_queryset(self):
        qs = TestCase.objects.select_related('project', 'module', 'created_by', 'updated_by').all()
        project_id = self.request.query_params.get('project')
        module_id = self.request.query_params.get('module')
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
            qs = qs.filter(type=type_filter)
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
