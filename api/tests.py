# from django.test import TestCase
# from django.urls import reverse
# from rest_framework.test import APIClient
# from django.contrib.auth.models import User
# from .models import Customer, Order

# class OrderAPITestCase(TestCase):
#     def setUp(self):
#         self.client = APIClient()
#         self.user = User.objects.create_user(
#             username='testuser', 
#             password='testpass123'
#         )
#         self.customer = Customer.objects.create(
#             user=self.user,
#             phone='+254700000000',
#             code='TEST001'
#         )
#         self.client.force_authenticate(user=self.user)

#     def test_create_order(self):
#         url = reverse('order-list')
#         data = {
#             'customer': self.customer.id,
#             'item': 'Test Product',
#             'amount': '100.00'
#         }
#         response = self.client.post(url, data, format='json')
#         self.assertEqual(response.status_code, 201)
#         self.assertEqual(Order.objects.count(), 1)

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from api.models import Customer

class APITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        user = User.objects.create_user(username='testuser', password='testpass')
        Customer.objects.create(user=user, phone='+254700000000', code='TEST001')

    def test_order_creation(self):
        # Get JWT token
        token_url = reverse('token_obtain_pair')
        response = self.client.post(token_url, {
            'username': 'testuser',
            'password': 'testpass'
        }, format='json')
        token = response.data['access']
        
        # Create order
        order_url = reverse('order-list')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.post(order_url, {
            "customer": 1,
            "item": "CI/CD Test Item",
            "amount": "99.99"
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['item'], "CI/CD Test Item")