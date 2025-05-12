from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Customer, Order
from .serializers import CustomerSerializer, OrderSerializer
from .services import send_sms_notification

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        order = serializer.save()
        message = f"Hello {order.customer.user.username}, your order for {order.item} (KSh{order.amount}) has been received."
        send_sms_notification(order.customer.phone, message)