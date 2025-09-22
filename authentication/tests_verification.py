from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core import mail
from rest_framework.test import APIClient
from .models import VerificationCode

class VerificationCodeTestCase(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(email='test@example.com', username='testuser', password='testpass')

    def test_verification_code_creation(self):
        code = '123456'
        vc = VerificationCode.objects.create(user=self.user, code=code)
        self.assertEqual(vc.code, code)
        self.assertFalse(vc.is_used)

    def test_verification_code_lookup(self):
        code = '654321'
        VerificationCode.objects.create(user=self.user, code=code)
        found = VerificationCode.objects.filter(user=self.user, code=code, is_used=False).first()
        self.assertIsNotNone(found)
        self.assertEqual(found.code, code)

    def test_verification_code_mark_used(self):
        code = '111222'
        vc = VerificationCode.objects.create(user=self.user, code=code)
        vc.is_used = True
        vc.save()
        found = VerificationCode.objects.filter(user=self.user, code=code, is_used=False).first()
        self.assertIsNone(found)

    def test_resend_verification_sends_email_and_creates_code(self):
        client = APIClient()
        url = '/api/auth/resend-verification/'
        response = client.post(url, {'user_id': self.user.id}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(VerificationCode.objects.filter(user=self.user).exists())
        self.assertGreaterEqual(len(mail.outbox), 1)
