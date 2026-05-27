from django.contrib import admin
from .models import TestRun, TestResult


class TestResultInline(admin.TabularInline):
    model = TestResult
    extra = 0
    fields = ['test_case', 'status', 'executed_by', 'executed_at']


@admin.register(TestRun)
class TestRunAdmin(admin.ModelAdmin):
    list_display = ['name', 'test_plan', 'status', 'assigned_to', 'started_at', 'completed_at', 'created_by', 'created_at']
    search_fields = ['name', 'test_plan__name']
    list_filter = ['status', 'test_plan']
    list_select_related = ['test_plan', 'assigned_to', 'created_by']
    date_hierarchy = 'created_at'


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ['test_run', 'test_case', 'status', 'executed_by', 'executed_at']
    search_fields = ['test_run__name', 'test_case__title']
    list_filter = ['status', 'test_run']
    list_select_related = ['test_run', 'test_case', 'executed_by']
    date_hierarchy = 'executed_at'
