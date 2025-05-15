from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Customer, Order
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()

class OrderAPITests(APITestCase):
    """
    Comprehensive test suite for Order API endpoints
    Includes all CRUD operations with authentication and validation tests
    """
    
    def setUp(self):
        """Initialize test data and authentication"""
        # Create test user
        self.user = User.objects.create_user(
            username='testcustomer',
            password='securepassword123',
            email='customer@example.com',
            first_name='Test',
            last_name='Customer'
        )
        
        # Create customer profile
        self.customer = Customer.objects.create(
            user=self.user,
            phone='+254712345678',
            code='CUST001'
        )
        
        # Create sample order
        self.order = Order.objects.create(
            customer=self.customer,
            item='Sample Product',
            amount='19.99'
        )
        
        # Generate JWT token
        self.token = str(AccessToken.for_user(self.user))
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    # --- CREATE OPERATION TESTS ---
    def test_create_order_authenticated(self):
        """Test successful order creation by authenticated customer"""
        url = reverse('order-list')
        data = {
            'item': 'New Product',
            'amount': '29.99',
            'customer': self.customer.id
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 2)
        self.assertEqual(response.data['item'], 'New Product')

    def test_create_order_unauthenticated(self):
        """Test order creation fails without authentication"""
        self.client.credentials()  # Remove auth
        
        response = self.client.post(
            reverse('order-list'),
            {'item': 'Test', 'amount': '10.00'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- READ OPERATION TESTS ---
    def test_list_orders(self):
        """Test retrieving all orders"""
        response = self.client.get(reverse('order-list'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.order.id)

    def test_retrieve_order_detail(self):
        """Test retrieving single order details"""
        url = reverse('order-detail', kwargs={'pk': self.order.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['item'], 'Sample Product')

    # --- UPDATE OPERATION TESTS ---
    def test_full_order_update(self):
        """Test complete order update using PUT"""
        url = reverse('order-detail', kwargs={'pk': self.order.pk})
        updated_data = {
            'item': 'Updated Product',
            'amount': '39.99',
            'customer': self.customer.id
        }
        
        response = self.client.put(url, updated_data, format='json')
        self.order.refresh_from_db()
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.order.item, 'Updated Product')

    def test_partial_order_update(self):
        """Test partial order update using PATCH"""
        url = reverse('order-detail', kwargs={'pk': self.order.pk})
        response = self.client.patch(
            url,
            {'amount': '49.99'},
            format='json'
        )
        self.order.refresh_from_db()
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(self.order.amount), '49.99')

    # --- DELETE OPERATION TESTS ---
    def test_order_deletion(self):
        """Test order deletion"""
        url = reverse('order-detail', kwargs={'pk': self.order.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Order.objects.count(), 0)

    # --- VALIDATION TESTS ---
    def test_invalid_order_data(self):
        """Test order creation with invalid data"""
        test_cases = [
            {'item': '', 'amount': '10.00'},  # Empty item
            {'item': 'A'*101, 'amount': '10.00'},  # Item too long
            {'item': 'Valid', 'amount': '-10.00'},  # Negative amount
            {'item': 'Valid', 'amount': 'not_a_number'}  # Invalid amount
        ]
        
        for data in test_cases:
            response = self.client.post(
                reverse('order-list'),
                data,
                format='json'
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- PERMISSION TESTS ---
    def test_customer_cannot_access_others_orders(self):
        """Test customers can't access other users' orders"""
        # Create second customer
        other_user = User.objects.create_user(
            username='othercustomer',
            password='password123'
        )
        other_customer = Customer.objects.create(
            user=other_user,
            phone='+254700000000',
            code='CUST002'
        )
        other_order = Order.objects.create(
            customer=other_customer,
            item='Other Product',
            amount='99.99'
        )
        
        # Try to access other customer's order
        url = reverse('order-detail', kwargs={'pk': other_order.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)



        # how to run test

        # python manage.py test api.tests.OrderAPITests --verbosity=2