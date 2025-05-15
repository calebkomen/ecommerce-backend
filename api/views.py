from rest_framework import viewsets, generics, status, permissions
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from .models import Customer, Order
from .serializers import (
    CustomerSerializer, 
    OrderSerializer,
    RegisterSerializer,
    UserSerializer
)
from .services import SMSService
import logging

logger = logging.getLogger(__name__)

class CustomerViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Customer.objects.all()  # Required for DefaultRouter

    def get_queryset(self):
        """Only return customers belonging to the current user"""
        return self.queryset.filter(user=self.request.user)

    def get_object(self):
        """Ensure users can only access their own customer profile"""
        obj = super().get_object()
        if obj.user != self.request.user:
            raise NotFound("Customer profile not found")
        return obj

    def perform_create(self, serializer):
        """Automatically associate customer with current user"""
        serializer.save(user=self.request.user)

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Order.objects.all()  # Required for DefaultRouter
    
    def get_queryset(self):
        """Only return orders belonging to the current user"""
        return self.queryset.filter(customer__user=self.request.user)

    def get_object(self):
        """Ensure users can only access their own orders"""
        obj = super().get_object()
        if obj.customer.user != self.request.user:
            raise NotFound("Order not found")
        return obj
    
    def perform_create(self, serializer):
        """Handle order creation with SMS notification"""
        customer = get_object_or_404(Customer, user=self.request.user)
        order = serializer.save(customer=customer)
        
        try:
            message = f"Hello {order.customer.user.username}, your order #{order.id} for {order.item} (KSh{order.amount}) has been received."
            sms_response = SMSService.send(order.customer.phone, message)
            if sms_response.get('status') == 'failed':
                logger.warning(f"Order #{order.id} created but SMS failed")
        except Exception as e:
            logger.error(f"Error processing order #{order.id}: {str(e)}")

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                "user": UserSerializer(user).data,
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            return Response(
                {"error": "Registration failed - username or customer code may already exist"},
                status=status.HTTP_400_BAD_REQUEST
            )

class UserProfileView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user