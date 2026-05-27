from django.test import TestCase
from django.contrib.auth.models import User
from apps.projects.models import Project, Module
from .models import TestCase as TestCaseModel, TestCaseStep


class TestCaseModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin', password='admin')
        self.project = Project.objects.create(name='P', created_by=self.user)
        self.module = Module.objects.create(project=self.project, name='M1')

    def test_create_testcase(self):
        tc = TestCaseModel.objects.create(
            project=self.project, module=self.module,
            title='TC1', created_by=self.user,
        )
        self.assertEqual(tc.priority, 'P2')
        self.assertEqual(tc.status, 'draft')

    def test_create_with_steps(self):
        tc = TestCaseModel.objects.create(
            project=self.project, module=self.module,
            title='TC2', created_by=self.user,
        )
        TestCaseStep.objects.create(test_case=tc, step_number=1, action='Click', expected_result='OK')
        TestCaseStep.objects.create(test_case=tc, step_number=2, action='Type', expected_result='Done')
        self.assertEqual(tc.steps.count(), 2)


class TestCaseAPITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin', password='admin')
        self.project = Project.objects.create(name='P', created_by=self.user)
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.auth = f'Bearer {self.token}'

    def test_auth_required(self):
        resp = self.client.get('/api/testcases/')
        self.assertEqual(resp.status_code, 401)

    def test_list_testcases(self):
        resp = self.client.get('/api/testcases/', HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(resp.status_code, 200)

    def test_filter_by_project(self):
        resp = self.client.get(f'/api/testcases/?project={self.project.id}', HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(resp.status_code, 200)
