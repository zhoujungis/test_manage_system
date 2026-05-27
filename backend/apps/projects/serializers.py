from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Project, Module, ProjectMember, ProjectTask, TestCaseAssignment, AssignmentAttachment


class ModuleSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    case_count = serializers.SerializerMethodField()

    class Meta:
        model = Module
        fields = ['id', 'project', 'parent', 'name', 'description', 'case_count', 'children']

    def get_case_count(self, obj):
        return getattr(obj, 'case_count', obj.testcases.count())

    def get_children(self, obj):
        if hasattr(obj, 'children'):
            return ModuleSerializer(obj.children.all(), many=True).data
        return []


class ProjectSerializer(serializers.ModelSerializer):
    module_count = serializers.SerializerMethodField()
    testcase_count = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    testplan_count = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()
    task_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'status', 'product_line', 'created_by', 'created_by_name',
                  'planned_start_date', 'planned_end_date', 'module_count', 'testcase_count',
                  'testplan_count', 'member_count', 'task_count', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at', 'created_by']

    def get_module_count(self, obj):
        return getattr(obj, 'module_count', obj.modules.count())

    def get_testcase_count(self, obj):
        return getattr(obj, 'testcase_count', obj.testcases.count())

    def get_testplan_count(self, obj):
        return getattr(obj, 'testplan_count', obj.testplans.count())

    def get_member_count(self, obj):
        return getattr(obj, 'member_count', obj.members.count())

    def get_task_count(self, obj):
        return getattr(obj, 'task_count', obj.tasks.count())

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.username
        return None


class ProjectMemberSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    role_label = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = ProjectMember
        fields = ['id', 'project', 'user', 'user_name', 'role', 'role_label', 'joined_at']
        read_only_fields = ['joined_at', 'project']

    def validate(self, data):
        project = self.context.get('project')
        user = data.get('user')
        if project and user:
            qs = ProjectMember.objects.filter(project=project, user=user)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError('该用户已是项目成员，请勿重复添加')
        return data


class ProjectTaskSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True, default=None)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default=None)
    status_label = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ProjectTask
        fields = ['id', 'project', 'title', 'round', 'description', 'assigned_to', 'assigned_to_name',
                  'status', 'status_label', 'priority', 'due_date', 'created_by', 'created_by_name',
                  'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'project']


class AssignmentAttachmentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    uploaded_by_name = serializers.CharField(source='uploaded_by.username', read_only=True, default=None)

    class Meta:
        model = AssignmentAttachment
        fields = [
            'id', 'assignment', 'file', 'file_url', 'original_name', 'file_size',
            'uploaded_by', 'uploaded_by_name', 'created_at',
        ]
        read_only_fields = ['id', 'assignment', 'file_url', 'original_name', 'file_size', 'uploaded_by', 'created_at']

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        if obj.file:
            return obj.file.url
        return None


class TestCaseAssignmentSerializer(serializers.ModelSerializer):
    attachments = AssignmentAttachmentSerializer(many=True, read_only=True)
    test_case_title = serializers.CharField(source='test_case.title', read_only=True)
    test_case_priority = serializers.CharField(source='test_case.priority', read_only=True)
    test_case_module = serializers.SerializerMethodField()
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True, default=None)
    status_label = serializers.CharField(source='get_status_display', read_only=True)
    approval_status_label = serializers.CharField(source='get_approval_status_display', read_only=True)
    task_title = serializers.CharField(source='task.title', read_only=True, default=None)
    task_round = serializers.CharField(source='task.round', read_only=True, default=None)

    class Meta:
        model = TestCaseAssignment
        fields = ['id', 'project', 'task', 'task_title', 'task_round',
                  'test_case', 'test_case_title', 'test_case_priority',
                  'test_case_module', 'assigned_to', 'assigned_to_name', 'status',
                  'status_label', 'approval_status', 'approval_status_label',
                  'notes', 'attachments', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at', 'project']

    def get_test_case_module(self, obj):
        return obj.test_case.module.name if obj.test_case.module else None

    def validate(self, data):
        project = self.context.get('project')
        task = data.get('task')
        if task and project and task.project_id != project.id:
            raise serializers.ValidationError('所选任务不属于当前项目')
        tc = data.get('test_case')
        au = data.get('assigned_to')
        if project and tc and au:
            qs = TestCaseAssignment.objects.filter(project=project, test_case=tc, assigned_to=au)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError('该用例已分配给该成员')
        return data


class TestCaseAssignmentTreeSerializer(serializers.ModelSerializer):
    test_case_title = serializers.CharField(source='test_case.title', read_only=True)
    test_case_priority = serializers.CharField(source='test_case.priority', read_only=True)
    test_case_module = serializers.CharField(source='test_case.module.name', read_only=True, default=None)
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True, default=None)
    task_title = serializers.CharField(source='task.title', read_only=True, default=None)
    task_round = serializers.CharField(source='task.round', read_only=True, default=None)

    class Meta:
        model = TestCaseAssignment
        fields = ['id', 'task', 'task_title', 'task_round',
                  'test_case', 'test_case_title', 'test_case_priority',
                  'test_case_module', 'assigned_to', 'assigned_to_name',
                  'status', 'approval_status', 'notes']
