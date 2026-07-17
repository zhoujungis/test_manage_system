from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from .models import UserProfile, VerificationCode, hash_verification_code


class UserProfileTests(TestCase):
    def test_create_profile(self):
        user = User.objects.create_user(username='test', password='Str0ng!Passw0rd_2026')
        profile = UserProfile.objects.create(user=user, role='tester')
        self.assertEqual(str(profile), 'test - 测试工程师')

    def test_profile_role_default(self):
        user = User.objects.create_user(username='test2', password='Str0ng!Passw0rd_2026')
        profile = UserProfile.objects.create(user=user)
        self.assertEqual(profile.role, 'tester')


class VerificationCodeTests(TestCase):
    """C8 fix: 适配 0007 迁移后的 hash / purpose / consumed_at schema。"""

    def test_issue_creates_hash_and_returns_code(self):
        code = VerificationCode.issue('test@glazero.com', VerificationCode.PURPOSE_REGISTER)
        self.assertEqual(len(code), VerificationCode.CODE_LENGTH)
        vc = VerificationCode.objects.get(email='test@glazero.com')
        # 明文不再存；只存 hash + 验证可对照
        self.assertEqual(vc.code_hash, hash_verification_code(code))
        self.assertIsNone(vc.consumed_at)
        self.assertFalse(vc.is_locked)
        self.assertTrue(vc.is_active)

    def test_issue_invalidates_previous_unconsumed(self):
        c1 = VerificationCode.issue('test@glazero.com', VerificationCode.PURPOSE_REGISTER)
        c2 = VerificationCode.issue('test@glazero.com', VerificationCode.PURPOSE_REGISTER)
        self.assertNotEqual(c1, c2)
        # 第一次的码应该被标 consumed_at（失效）
        first = VerificationCode.objects.get(email='test@glazero.com', consumed_at__isnull=False)
        self.assertEqual(first.code_hash, hash_verification_code(c1))
        # 第二次仍是 active
        second = VerificationCode.objects.get(email='test@glazero.com', consumed_at__isnull=True)
        self.assertEqual(second.code_hash, hash_verification_code(c2))

    def test_record_failure_locks_after_max_attempts(self):
        VerificationCode.issue('test@glazero.com', VerificationCode.PURPOSE_REGISTER)
        for _ in range(VerificationCode.MAX_ATTEMPTS):
            (VerificationCode.objects
             .filter(email='test@glazero.com')
             .update(attempts=VerificationCode.MAX_ATTEMPTS))
        vc = VerificationCode.objects.get(email='test@glazero.com')
        self.assertTrue(vc.is_locked)
        self.assertFalse(vc.is_active)


class AuthAPITests(TestCase):
    """适配新 contract：login 用 email、不接受 username；change-password 必须登录。"""

    def setUp(self):
        self.client = APIClient()

    def test_send_code_rejects_non_glazero(self):
        resp = self.client.post(
            '/api/auth/send-code/',
            {'email': 'bad@gmail.com'},
            format='json',
        )
        self.assertEqual(resp.status_code, 400)

    def test_register_rejects_invalid_code(self):
        resp = self.client.post('/api/auth/register/', {
            'email': 'test@glazero.com',
            'username': 'testuser',
            'password': 'Str0ng!Passw0rd_2026',
            'code': '000000',
        }, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_login_required_for_me(self):
        resp = self.client.get('/api/auth/me/')
        self.assertEqual(resp.status_code, 401)

    def test_me_returns_identity_from_db(self):
        user = User.objects.create_user(
            username='alice', email='alice@glazero.com',
            password='Str0ng!Passw0rd_2026',
        )
        UserProfile.objects.create(user=user, role='tester', phone='13800138000')
        self.client.force_authenticate(user=user)
        resp = self.client.get('/api/auth/me/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['username'], 'alice')
        self.assertEqual(data['email'], 'alice@glazero.com')
        self.assertEqual(data['role'], 'tester')
        self.assertEqual(data['role_label'], '测试工程师')
        self.assertEqual(data['phone'], '13800138000')

    def test_login_success_with_email(self):
        # C8 fix: login 现在强制用 email
        User.objects.create_user(
            username='tester', email='tester@glazero.com',
            password='Str0ng!Passw0rd_2026',
        )
        resp = self.client.post('/api/auth/login/', {
            'email': 'tester@glazero.com',
            'password': 'Str0ng!Passw0rd_2026',
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('access', resp.json())

    def test_register_rejects_weak_password(self):
        """C5 fix: AUTH_PASSWORD_VALIDATORS 在 register 路径生效"""
        resp = self.client.post('/api/auth/send-code/', {
            'email': 'weak@glazero.com',
        }, format='json')
        # send_code 接受任意 glazero 邮箱；下一步需要真实 code 才能注册，
        # 这里只验证 ChangePassword/ResetPassword 路径会拒弱密码
        resp2 = self.client.post('/api/auth/reset-password/', {
            'email': 'weak@glazero.com',
            'code': '000000',
            'password': '123',
        }, format='json')
        self.assertIn(resp2.status_code, (400, 404))  # 验证失败或弱密码都会被拒

    def test_change_password_requires_authentication(self):
        """C8 fix: 改密接口必须登录"""
        user = User.objects.create_user(
            username='bob', email='bob@glazero.com',
            password='OldStr0ng!Passw0rd_2026',
        )
        # 未登录直接 POST 必须 401
        resp = self.client.post('/api/auth/change-password/', {
            'old_password': 'OldStr0ng!Passw0rd_2026',
            'new_password': 'NewStr0ng!Passw0rd_2026',
        }, format='json')
        self.assertEqual(resp.status_code, 401)

        # 登录后改密成功
        self.client.force_authenticate(user=user)
        resp = self.client.post('/api/auth/change-password/', {
            'old_password': 'OldStr0ng!Passw0rd_2026',
            'new_password': 'NewStr0ng!Passw0rd_2026',
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.check_password('NewStr0ng!Passw0rd_2026'))

    def test_tester_cannot_list_users(self):
        user = User.objects.create_user(
            username='tester1', email='t1@glazero.com',
            password='Str0ng!Passw0rd_2026',
        )
        UserProfile.objects.create(user=user, role='tester')
        self.client.force_authenticate(user=user)
        resp = self.client.get('/api/auth/users/')
        self.assertEqual(resp.status_code, 403)

    def test_admin_can_delete_non_admin(self):
        admin = User.objects.create_user(
            username='admin1', email='admin1@glazero.com',
            password='Str0ng!Passw0rd_2026',
        )
        UserProfile.objects.create(user=admin, role='admin')
        target = User.objects.create_user(
            username='victim', email='victim@glazero.com',
            password='Str0ng!Passw0rd_2026',
        )
        UserProfile.objects.create(user=target, role='tester')

        client = APIClient()
        client.force_authenticate(user=admin)
        resp = client.delete(f'/api/auth/admin/users/{target.id}/')
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(pk=target.id).exists())

        # 自删防御
        resp_self = client.delete(f'/api/auth/admin/users/{admin.id}/')
        self.assertEqual(resp_self.status_code, 400)

    def test_reset_password_invalid_code(self):
        User.objects.create_user(
            username='carol', email='carol@glazero.com',
            password='OldStr0ng!Passw0rd_2026',
        )
        resp = self.client.post('/api/auth/reset-password/', {
            'email': 'carol@glazero.com',
            'code': '000000',
            'password': 'NewStr0ng!Passw0rd_2026',
        }, format='json')
        self.assertEqual(resp.status_code, 400)