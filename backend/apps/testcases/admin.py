from django.contrib import admin
from .models import TestCase, TestCaseStep


class TestCaseStepInline(admin.TabularInline):
    model = TestCaseStep
    extra = 0


@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'project', 'module', 'priority', 'type', 'status', 'created_by', 'created_at']
    search_fields = ['title', 'description']
    list_filter = ['priority', 'type', 'status', 'product_line', 'project']
    list_select_related = ['project', 'module', 'created_by']
    date_hierarchy = 'created_at'
    inlines = [TestCaseStepInline]


@admin.register(TestCaseStep)
class TestCaseStepAdmin(admin.ModelAdmin):
    list_display = ['test_case', 'step_number', 'action', 'expected_result']
    search_fields = ['action', 'expected_result']
    list_select_related = ['test_case']
