from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from django.core import mail
from django.contrib.auth import get_user_model

@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class AuthEmailTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.User = get_user_model()

    def test_register_sends_verification_email(self):
        payload = {
            'name': 'Test User',
            'email': 'new@example.com',
            'phonenumber': '1234567890',
            'location': 'Kigali',
            'password': 'StrongPass!23'
        }
        response = self.client.post('/api/auth/register/', payload, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertGreaterEqual(len(mail.outbox), 1)
        self.assertIn('Verify Your Email - Lost and Found Tracker', mail.outbox[-1].subject)

    def test_resend_verification_uses_user_id(self):
        user = self.User.objects.create_user(email='resend@example.com', username='resend', password='pass')
        response = self.client.post('/api/auth/resend-verification/', {'user_id': user.id}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(mail.outbox), 1)
        subjects = [m.subject for m in mail.outbox]
        self.assertTrue(any('Verify Your Email - Lost and Found Tracker' in s for s in subjects))
from django.contrib.auth import get_user_model
from .models import VerificationCode

class VerificationCodeTests(TestCase):
	def setUp(self):
		self.user = get_user_model().objects.create_user(email='test@example.com', username='testuser', password='testpass')
		self.code = VerificationCode.objects.create(user=self.user, code='123456')

	def test_verify_code_success(self):
		result = VerificationCode.verify_code(email='test@example.com', code='123456')
		self.assertTrue(result)
		self.code.refresh_from_db()
		self.assertTrue(self.code.is_used)

	def test_verify_code_fail(self):
		result = VerificationCode.verify_code(email='test@example.com', code='000000')
		self.assertFalse(result)

	def test_resend_code(self):
		new_code = VerificationCode.resend_code(email='test@example.com')
		self.assertEqual(len(new_code), 6)
		vc = VerificationCode.objects.get(user=self.user)
		self.assertEqual(vc.code, new_code)
		self.assertFalse(vc.is_used)
from django.test import TestCase

# Create your tests here.
