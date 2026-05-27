from django.test import TestCase
from django.contrib.auth.models import User
from apps.projects.models import Project
from apps.testcases.models import TestCase as TestCaseModel
from .models import TestPlan, TestPlanCase


class TestPlanModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin', password='admin')
        self.project = Project.objects.create(name='P', created_by=self.user)
        self.tc = TestCaseModel.objects.create(title='TC1', project=self.project, created_by=self.user)

    def test_create_testplan(self):
        tp = TestPlan.objects.create(project=self.project, name='Plan1', created_by=self.user)
        self.assertEqual(str(tp), 'Plan1')
        self.assertEqual(tp.status, 'draft')

    def test_add_cases_to_plan(self):
        tp = TestPlan.objects.create(project=self.project, name='Plan1', created_by=self.user)
        tpc = TestPlanCase.objects.create(test_plan=tp, test_case=self.tc, order=1)
        self.assertEqual(tpc.order, 1)
        self.assertEqual(tp.plan_cases.count(), 1)


class TestPlanAPITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin', password='admin')
        self.project = Project.objects.create(name='P', created_by=self.user)
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.auth = f'Bearer {self.token}'

    def test_auth_required(self):
        resp = self.client.get('/api/testplans/')
        self.assertEqual(resp.status_code, 401)

    def test_list_plans(self):
        resp = self.client.get('/api/testplans/', HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(resp.status_code, 200)
