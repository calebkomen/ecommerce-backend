from rest_framework import viewsets, generics, status, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.db import IntegrityError
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
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        order = serializer.save()
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
                {"error": "Registration failed - possibly duplicate data"},
                status=status.HTTP_400_BAD_REQUEST
            )

class UserProfileView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user