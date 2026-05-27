from django.test import TestCase
from django.contrib.auth.models import User
from .models import Project, Module, ProjectMember, ProjectTask, TestCaseAssignment
from apps.testcases.models import TestCase as TestCaseModel


class ProjectModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin', password='admin')

    def test_create_project(self):
        p = Project.objects.create(name='TestProject', created_by=self.user)
        self.assertEqual(str(p), 'TestProject')
        self.assertEqual(p.status, 'active')

    def test_unique_name(self):
        Project.objects.create(name='Project1', created_by=self.user)
        with self.assertRaises(Exception):
            Project.objects.create(name='Project1', created_by=self.user)


class ModuleModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin', password='admin')
        self.project = Project.objects.create(name='P', created_by=self.user)

    def test_create_module(self):
        m = Module.objects.create(project=self.project, name='Mod1')
        self.assertEqual(str(m), 'Mod1')

    def test_module_parent_child(self):
        parent = Module.objects.create(project=self.project, name='Parent')
        child = Module.objects.create(project=self.project, name='Child', parent=parent)
        self.assertEqual(child.parent, parent)
        self.assertIn(child, parent.children.all())


class ProjectMemberTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin', password='admin')
        self.member = User.objects.create_user(username='member', password='member')
        self.project = Project.objects.create(name='P', created_by=self.user)

    def test_create_member(self):
        pm = ProjectMember.objects.create(project=self.project, user=self.member, role='tester')
        self.assertEqual(pm.get_role_display(), '测试人员')


class ProjectAPITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin', password='admin')
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.auth = f'Bearer {self.token}'

    def test_auth_required(self):
        resp = self.client.get('/api/projects/')
        self.assertEqual(resp.status_code, 401)

    def test_list_projects(self):
        Project.objects.create(name='P1', created_by=self.user)
        resp = self.client.get('/api/projects/', HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(resp.status_code, 200)

    def test_create_project(self):
        resp = self.client.post('/api/projects/', {
            'name': 'NewProject',
        }, content_type='application/json', HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json()['name'], 'NewProject')
