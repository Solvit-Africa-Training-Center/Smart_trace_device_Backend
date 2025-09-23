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

    def test_lostitem_by_email_endpoint(self):
        LostItem.objects.create(title='Thing1', category='Phone', serial_number='A1', first_name='Jon', loster_email='lost@example.com')
        LostItem.objects.create(title='Thing2', category='Laptop', serial_number='A2', loster_email='lost@example.com')
        LostItem.objects.create(title='Thing3', category='Tablet', serial_number='A3', loster_email='other@example.com')
        resp = self.client.get('/api/devices/lost/by-email/', {'email': 'lost@example.com'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 2)
        emails = set([item.get('losterEmail') for item in resp.data])
        self.assertEqual(emails, {'lost@example.com'})

    def test_founditem_by_email_endpoint(self):
        FoundItem.objects.create(name='PhoneX', category='Phone', serial_number='B1', founder_email='finder@example.com')
        FoundItem.objects.create(name='PhoneY', category='Phone', serial_number='B2', founder_email='finder@example.com')
        FoundItem.objects.create(name='PhoneZ', category='Phone', serial_number='B3', founder_email='other@example.com')
        resp = self.client.get('/api/devices/found/by-email/', {'email': 'finder@example.com'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 2)
        emails = set([item.get('founderEmail') for item in resp.data])
        self.assertEqual(emails, {'finder@example.com'})

    def test_match_list_output_contains_requested_fields(self):
        lost = LostItem.objects.create(title='Macbook', category='Laptop', serial_number='SN-MAC', first_name='Alice', last_name='L', phone_number='123', loster_email='alice@example.com')
        found = FoundItem.objects.create(name='Macbook Pro', category='Laptop', serial_number='SN-MAC', reporter_first_name='Bob', reporter_last_name='K', phone_number='456', founder_email='bob@example.com')
        Match.objects.create(lost_item=lost, found_item=found, match_status='unclaimed')
        resp = self.client.get('/api/devices/matches/list/')
        self.assertEqual(resp.status_code, 200)
        self.assertGreaterEqual(len(resp.data), 1)
        first = resp.data[0]
        self.assertIn('matched', first)
        matched = first['matched']
        self.assertIn('loster', matched)
        self.assertIn('founder', matched)
        self.assertEqual(matched['loster']['email'], 'alice@example.com')
        self.assertEqual(matched['founder']['email'], 'bob@example.com')
        self.assertEqual(matched['serial_number'], 'SN-MAC')
        self.assertTrue(matched['device_name'] in ['Macbook Pro', 'Macbook'])
