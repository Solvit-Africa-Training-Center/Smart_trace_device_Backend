from django.test import TestCase

# Create your tests here.
from django.contrib.auth import get_user_model
from .models import VerificationCode

class VerificationCodeTests(TestCase):
	def setUp(self):
		self.user = get_user_model().objects.create_user(email='test@example.com', username='testuser', password='testpass')
		self.code = VerificationCode.objects.create(user=self.user, email=self.user.email, code='123456')

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
		vc = VerificationCode.objects.get(email='test@example.com')
		self.assertEqual(vc.code, new_code)
		self.assertFalse(vc.is_used)
from django.test import TestCase

# Create your tests here.
