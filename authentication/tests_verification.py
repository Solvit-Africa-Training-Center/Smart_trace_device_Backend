from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import VerificationCode

class VerificationCodeTestCase(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(email='test@example.com', username='testuser', password='testpass')

    def test_verification_code_creation(self):
        code = '123456'
        vc = VerificationCode.objects.create(user=self.user, email=self.user.email, code=code)
        self.assertEqual(vc.code, code)
        self.assertEqual(vc.email, self.user.email)
        self.assertFalse(vc.is_used)

    def test_verification_code_lookup(self):
        code = '654321'
        VerificationCode.objects.create(user=self.user, email=self.user.email, code=code)
        found = VerificationCode.objects.filter(email=self.user.email, code=code, is_used=False).first()
        self.assertIsNotNone(found)
        self.assertEqual(found.code, code)

    def test_verification_code_mark_used(self):
        code = '111222'
        vc = VerificationCode.objects.create(user=self.user, email=self.user.email, code=code)
        vc.is_used = True
        vc.save()
        found = VerificationCode.objects.filter(email=self.user.email, code=code, is_used=False).first()
        self.assertIsNone(found)
