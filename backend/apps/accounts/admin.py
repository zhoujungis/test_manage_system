from django.contrib import admin
from .models import UserProfile, VerificationCode


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone']
    search_fields = ['user__username', 'phone']
    list_filter = ['role']
    list_select_related = ['user']
    list_per_page = 50
    show_full_result_count = False


@admin.register(VerificationCode)
class VerificationCodeAdmin(admin.ModelAdmin):
    # C3 重写后：不再存明文 code / is_used。
    # SECURITY: 严禁把 code_hash 显示给管理员（攻击面已经包含 DBA / admin 用户）。
    list_display = ['email', 'purpose', 'attempts', 'created_at', 'consumed_at']
    search_fields = ['email']
    list_filter = ['purpose']
    date_hierarchy = 'created_at'
    readonly_fields = ['code_hash']   # 仅展示，不可改
    ordering = ['-created_at']        # 默认按时间倒序，方便排查最近的发送/验证
    list_per_page = 50
    show_full_result_count = False
