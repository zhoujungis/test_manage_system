from django.test import TestCase
from django.contrib.auth.models import User
from apps.projects.models import Project
from apps.testcases.models import TestCase as TestCaseModel
from apps.testplans.models import TestPlan
from .models import TestRun, TestResult


class TestRunModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin', password='admin')
        self.project = Project.objects.create(name='P', created_by=self.user)
        self.tp = TestPlan.objects.create(project=self.project, name='Plan1', created_by=self.user)
        self.tc = TestCaseModel.objects.create(title='TC1', project=self.project, created_by=self.user)

    def test_create_testrun(self):
        tr = TestRun.objects.create(test_plan=self.tp, name='Run1', created_by=self.user)
        self.assertEqual(tr.status, 'pending')

    def test_create_testresult(self):
        tr = TestRun.objects.create(test_plan=self.tp, name='Run1', created_by=self.user)
        result = TestResult.objects.create(test_run=tr, test_case=self.tc)
        self.assertEqual(result.status, 'pending')

    def test_unique_together(self):
        tr = TestRun.objects.create(test_plan=self.tp, name='Run1', created_by=self.user)
        TestResult.objects.create(test_run=tr, test_case=self.tc)
        with self.assertRaises(Exception):
            TestResult.objects.create(test_run=tr, test_case=self.tc)

    def test_start_rejects_non_pending(self):
        tr = TestRun.objects.create(test_plan=self.tp, name='Run1', created_by=self.user)
        tr.status = 'completed'
        tr.save()
        # completed run should reject start via API
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.user)
        token = str(refresh.access_token)
        resp = self.client.post(f'/api/testruns/{tr.id}/start/', HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(resp.status_code, 400)
