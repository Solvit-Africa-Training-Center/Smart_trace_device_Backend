from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from devices.models import LostItem, FoundItem

@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class ReportsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        LostItem.objects.create(title='Lost Phone', category='Phone', city_town='Kigali')
        LostItem.objects.create(title='Lost Laptop', category='Laptop', city_town='Kigali')
        FoundItem.objects.create(name='Phone', category='Phone', district='Gasabo')

    def test_location_stats(self):
        response = self.client.get('/api/reports/stats/location/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('lost', response.data)
        self.assertIn('found', response.data)
