from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TestCaseViewSet, testcase_tree

router = DefaultRouter()
router.register(r'testcases', TestCaseViewSet, basename='testcase')

urlpatterns = [
    path('', include(router.urls)),
    path('testcases-tree/', testcase_tree, name='testcase_tree'),
]
