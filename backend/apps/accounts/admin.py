from django.contrib import admin
from .models import UserProfile, VerificationCode


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone']
    search_fields = ['user__username', 'phone']
    list_filter = ['role']
    list_select_related = ['user']


@admin.register(VerificationCode)
class VerificationCodeAdmin(admin.ModelAdmin):
    list_display = ['email', 'code', 'is_used', 'created_at']
    search_fields = ['email', 'code']
    list_filter = ['is_used']
    date_hierarchy = 'created_at'
