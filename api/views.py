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
    queryset = Customer.objects.all()

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def get_object(self):
        obj = super().get_object()
        if obj.user != self.request.user:
            raise NotFound("Customer profile not found")
        return obj

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Order.objects.all()
    
    def get_queryset(self):
        return self.queryset.filter(customer__user=self.request.user)

    def get_object(self):
        obj = super().get_object()
        if obj.customer.user != self.request.user:
            raise NotFound("Order not found")
        return obj
    
    def perform_create(self, serializer):
        customer = get_object_or_404(Customer, user=self.request.user)
        order = serializer.save(customer=customer)
        
        # Enhanced SMS verification with detailed logging
        try:
            message = f"Hello {order.customer.user.username}, your order #{order.id} for {order.item} (KSh{order.amount}) has been received."
            
            # Test SMS in development
            if settings.DEBUG:
                logger.info(f"[DEV] SMS would be sent to {order.customer.phone}: {message}")
                sms_response = {'status': 'dev_success'}
            else:
                sms_response = SMSService.send(order.customer.phone, message)
            
            # Log full response
            logger.info(f"SMS attempt for order #{order.id}. Status: {sms_response.get('status')}. Response: {sms_response}")
            
            # Verify successful SMS delivery
            if sms_response.get('status') != 'success':
                logger.error(f"SMS failed for order #{order.id}. Response: {sms_response}")
                
        except Exception as e:
            logger.error(f"SMS error for order #{order.id}: {str(e)}", exc_info=True)
            # Continue with order creation even if SMS fails

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