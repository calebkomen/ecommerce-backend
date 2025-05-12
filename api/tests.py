from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from .models import Customer, Order

class OrderAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpass123'
        )
        self.customer = Customer.objects.create(
            user=self.user,
            phone='+254700000000',
            code='TEST001'
        )
        self.client.force_authenticate(user=self.user)

    def test_create_order(self):
        url = reverse('order-list')
        data = {
            'customer': self.customer.id,
            'item': 'Test Product',
            'amount': '100.00'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Order.objects.count(), 1)