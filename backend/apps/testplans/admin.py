from django.contrib import admin
from .models import TestPlan, TestPlanCase


class TestPlanCaseInline(admin.TabularInline):
    model = TestPlanCase
    extra = 0
    list_select_related = ['test_case']


@admin.register(TestPlan)
class TestPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'status', 'start_date', 'end_date', 'created_by', 'created_at']
    search_fields = ['name', 'project__name']
    list_filter = ['status', 'project']
    list_select_related = ['project', 'created_by']
    date_hierarchy = 'created_at'
    inlines = [TestPlanCaseInline]


@admin.register(TestPlanCase)
class TestPlanCaseAdmin(admin.ModelAdmin):
    list_display = ['test_plan', 'test_case', 'order']
    search_fields = ['test_plan__name', 'test_case__title']
    list_filter = ['test_plan']
    list_select_related = ['test_plan', 'test_case']
