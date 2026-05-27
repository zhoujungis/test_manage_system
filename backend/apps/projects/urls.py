from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, ModuleViewSet, ProjectMemberViewSet, ProjectTaskViewSet, TestCaseAssignmentViewSet, library_modules

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'modules', ModuleViewSet, basename='module')
router.register(r'project-members', ProjectMemberViewSet, basename='project-member')
router.register(r'project-tasks', ProjectTaskViewSet, basename='project-task')
router.register(r'case-assignments', TestCaseAssignmentViewSet, basename='case-assignment')

urlpatterns = [
    path('', include(router.urls)),
    path('library-modules/', library_modules, name='library_modules'),
]
