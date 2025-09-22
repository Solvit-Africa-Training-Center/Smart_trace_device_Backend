from django.test import TestCase, override_settings
from django.core import mail
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from .models import LostItem, FoundItem, Match


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class DeviceTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.User = get_user_model()
        self.user = self.User.objects.create_user(email='owner@example.com', username='owner', password='pass')

    def test_founditem_create_triggers_match_and_emails(self):
        lost = LostItem.objects.create(title='Lost Phone', category='Phone', serial_number='SN123', user=None, status='lost', first_name='John', loster_email='john@example.com')
        payload = {
            'name': 'iPhone',
            'category': 'Phone',
            'serialnumber': 'SN123',
            'founderEmail': 'finder@example.com'
        }
        response = self.client.post('/api/devices/found/', payload, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Match.objects.filter(lost_item=lost).exists())
        self.assertGreaterEqual(len(mail.outbox), 1)
        # Check subjects to both parties
        subjects = [m.subject for m in mail.outbox]
        self.assertTrue(any('Good News! Your Lost Item May Have Been Found' in s for s in subjects))
        self.assertTrue(any('Thank You! Your Found Item Report May Help Someone' in s for s in subjects))

    def test_lostitem_create_inverse_match_and_emails(self):
        FoundItem.objects.create(name='iPhone', category='Phone', serial_number='SN999', founder_email='finder2@example.com', status='found')
        payload = {
            'title': 'My Phone',
            'category': 'Phone',
            'serialNumber': 'SN999',
            'firstName': 'Alice',
            'losterEmail': 'alice@example.com'
        }
        response = self.client.post('/api/devices/lost/', payload, format='json')
        self.assertEqual(response.status_code, 201)
        lost_id = response.data.get('id')
        self.assertTrue(Match.objects.filter(lost_item_id=lost_id).exists())
        self.assertGreaterEqual(len(mail.outbox), 1)
        subjects = [m.subject for m in mail.outbox]
        self.assertTrue(any('Possible Match Found for Your Lost Item' in s for s in subjects))
        self.assertTrue(any('Potential Owner Located for the Found Item' in s for s in subjects))
