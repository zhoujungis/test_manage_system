from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .serializers import CustomTokenObtainPairSerializer
from .throttles import LoginRateThrottle
from . import views


class ThrottledTokenObtainPairView(TokenObtainPairView):
    throttle_classes = [LoginRateThrottle]
    serializer_class = CustomTokenObtainPairSerializer


urlpatterns = [
    path('login/', ThrottledTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', views.register, name='register'),
    path('send-code/', views.send_code, name='send_code'),
    path('send-reset-code/', views.send_reset_code, name='send_reset_code'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('change-password/', views.change_password, name='change_password'),
    path('me/', views.me, name='me'),
    path('users/', views.user_list, name='user_list'),
    path('admin/permissions/', views.admin_user_permissions, name='admin_user_permissions'),
    path('admin/users/', views.admin_create_user, name='admin_create_user'),
    path('admin/users/<int:user_id>/permissions/', views.admin_update_user_permissions, name='admin_update_user_permissions'),
    path('admin/users/<int:user_id>/', views.admin_delete_user, name='admin_delete_user'),
]
