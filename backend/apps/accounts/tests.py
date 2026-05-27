from django.test import TestCase
from django.contrib.auth.models import User
from .models import UserProfile, VerificationCode


class UserProfileTests(TestCase):
    def test_create_profile(self):
        user = User.objects.create_user(username='test', password='test')
        profile = UserProfile.objects.create(user=user, role='tester')
        self.assertEqual(str(profile), 'test - 测试工程师')

    def test_profile_role_default(self):
        user = User.objects.create_user(username='test2', password='test')
        profile = UserProfile.objects.create(user=user)
        self.assertEqual(profile.role, 'tester')


class VerificationCodeTests(TestCase):
    def test_create_code(self):
        vc = VerificationCode.objects.create(email='test@glazero.com', code='123456')
        self.assertFalse(vc.is_used)
        self.assertIsNotNone(vc.created_at)

    def test_code_mark_used(self):
        vc = VerificationCode.objects.create(email='test@glazero.com', code='123456')
        vc.is_used = True
        vc.save()
        vc.refresh_from_db()
        self.assertTrue(vc.is_used)


class AuthAPITests(TestCase):
    def test_send_code_rejects_non_glazero(self):
        resp = self.client.post('/api/auth/send-code/', {'email': 'bad@gmail.com'}, content_type='application/json')
        self.assertEqual(resp.status_code, 400)

    def test_register_rejects_invalid_code(self):
        resp = self.client.post('/api/auth/register/', {
            'email': 'test@glazero.com',
            'username': 'testuser',
            'password': 'testpass123',
            'code': '000000',
        }, content_type='application/json')
        self.assertEqual(resp.status_code, 400)

    def test_login_required_for_me(self):
        resp = self.client.get('/api/auth/me/')
        self.assertEqual(resp.status_code, 401)

    def test_me_returns_identity_from_db(self):
        user = User.objects.create_user(
            username='alice', email='alice@glazero.com', password='testpass123'
        )
        UserProfile.objects.create(user=user, role='tester', phone='13800138000')
        self.client.force_login(user)
        resp = self.client.get('/api/auth/me/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['username'], 'alice')
        self.assertEqual(data['email'], 'alice@glazero.com')
        self.assertEqual(data['role'], 'tester')
        self.assertEqual(data['role_label'], '测试工程师')
        self.assertEqual(data['phone'], '13800138000')
        self.assertIn('date_joined', data)

    def test_login_success(self):
        User.objects.create_user(username='tester', password='testpass123')
        resp = self.client.post('/api/auth/login/', {
            'email': '',
            'username': 'tester',
            'password': 'testpass123',
        }, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('access', resp.json())

    def test_change_password_wrong_old(self):
        User.objects.create_user(
            username='bob', email='bob@glazero.com', password='oldpass123'
        )
        resp = self.client.post('/api/auth/change-password/', {
            'email': 'bob@glazero.com',
            'old_password': 'wrong',
            'new_password': 'newpass123',
        }, content_type='application/json')
        self.assertEqual(resp.status_code, 400)

    def test_change_password_success(self):
        user = User.objects.create_user(
            username='bob', email='bob@glazero.com', password='oldpass123'
        )
        resp = self.client.post('/api/auth/change-password/', {
            'email': 'bob@glazero.com',
            'old_password': 'oldpass123',
            'new_password': 'newpass456',
        }, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.check_password('newpass456'))

    def test_tester_cannot_list_users(self):
        user = User.objects.create_user(
            username='tester1', email='t1@glazero.com', password='pass123456'
        )
        UserProfile.objects.create(user=user, role='tester')
        self.client.force_authenticate(user=user)
        resp = self.client.get('/api/auth/users/')
        self.assertEqual(resp.status_code, 403)

    def test_admin_delete_user(self):
        from rest_framework.test import APIClient

        admin = User.objects.create_user(username='admin1', password='pass123456')
        UserProfile.objects.create(user=admin, role='admin')
        target = User.objects.create_user(username='victim', password='pass123456')
        UserProfile.objects.create(user=target, role='tester')

        client = APIClient()
        client.force_authenticate(user=admin)
        resp = client.delete(f'/api/auth/admin/users/{target.id}/')
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(pk=target.id).exists())

        resp_self = client.delete(f'/api/auth/admin/users/{admin.id}/')
        self.assertEqual(resp_self.status_code, 400)

    def test_reset_password_invalid_code(self):
        User.objects.create_user(
            username='carol', email='carol@glazero.com', password='oldpass123'
        )
        resp = self.client.post('/api/auth/reset-password/', {
            'email': 'carol@glazero.com',
            'code': '000000',
            'password': 'newpass789',
        }, content_type='application/json')
        self.assertEqual(resp.status_code, 400)
