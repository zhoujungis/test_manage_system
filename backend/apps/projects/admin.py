from django.contrib import admin
from .models import Project, Module, ProjectMember, ProjectTask, TestCaseAssignment, AssignmentAttachment


# M5 fix: 统一给 list 较多的 admin 加 list_per_page=50 + show_full_result_count=False，
# 避免大表点 "Count" 触发全表 COUNT(*)。
_ADMIN_DEFAULTS = {'list_per_page': 50, 'show_full_result_count': False}


@admin.register(AssignmentAttachment)
class AssignmentAttachmentAdmin(admin.ModelAdmin):
    list_display = ['original_name', 'assignment', 'uploaded_by', 'file_size', 'created_at']
    list_select_related = ['assignment', 'uploaded_by']
    show_full_result_count = False
    list_per_page = 50


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'product_line', 'created_by', 'created_at']
    search_fields = ['name', 'description']
    list_filter = ['status', 'product_line']
    list_select_related = ['created_by']
    date_hierarchy = 'created_at'
    show_full_result_count = False
    list_per_page = 50


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'parent']
    search_fields = ['name']
    list_filter = ['project']
    list_select_related = ['project', 'parent']
    show_full_result_count = False
    list_per_page = 50


@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = ['project', 'user', 'role', 'joined_at']
    search_fields = ['user__username', 'project__name']
    list_filter = ['role', 'project']
    list_select_related = ['project', 'user']
    date_hierarchy = 'joined_at'
    show_full_result_count = False
    list_per_page = 50


@admin.register(ProjectTask)
class ProjectTaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'assigned_to', 'status', 'priority', 'due_date', 'created_at']
    search_fields = ['title', 'project__name']
    list_filter = ['status', 'priority', 'project']
    list_select_related = ['project', 'assigned_to']
    date_hierarchy = 'created_at'
    show_full_result_count = False
    list_per_page = 50


@admin.register(TestCaseAssignment)
class TestCaseAssignmentAdmin(admin.ModelAdmin):
    list_display = ['test_case', 'project', 'assigned_to', 'status', 'approval_status', 'created_at']
    search_fields = ['test_case__title', 'assigned_to__username', 'project__name']
    list_filter = ['status', 'approval_status', 'project']
    list_select_related = ['test_case', 'project', 'assigned_to']
    date_hierarchy = 'created_at'
    show_full_result_count = False
    list_per_page = 50
