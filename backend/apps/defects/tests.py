from django.test import TestCase
from django.contrib.auth.models import User
from apps.projects.models import Project
from .models import Defect


class DefectModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin', password='admin')
        self.project = Project.objects.create(name='P', created_by=self.user)

    def test_create_defect(self):
        d = Defect.objects.create(
            project=self.project, title='Bug1',
            description='Something broke', created_by=self.user,
        )
        self.assertEqual(d.severity, 'S2')
        self.assertEqual(d.status, 'open')
        self.assertEqual(str(d), '[S2-一般] Bug1')

    def test_severity_choices(self):
        d = Defect.objects.create(
            project=self.project, title='Critical',
            description='Urgent', severity='S0', created_by=self.user,
        )
        self.assertEqual(d.get_severity_display(), 'S0-致命')


class DefectAPITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin', password='admin')
        self.project = Project.objects.create(name='P', created_by=self.user)
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.auth = f'Bearer {self.token}'

    def test_auth_required(self):
        resp = self.client.get('/api/defects/')
        self.assertEqual(resp.status_code, 401)

    def test_list_defects(self):
        resp = self.client.get('/api/defects/', HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(resp.status_code, 200)
