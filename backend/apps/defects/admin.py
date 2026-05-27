from django.contrib import admin
from .models import Defect


@admin.register(Defect)
class DefectAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'severity', 'status', 'assigned_to', 'created_by', 'created_at']
    search_fields = ['title', 'description', 'project__name']
    list_filter = ['severity', 'status', 'project']
    list_select_related = ['project', 'assigned_to', 'created_by']
    date_hierarchy = 'created_at'
