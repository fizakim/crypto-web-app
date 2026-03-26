from django.db import models
from django.contrib.auth.models import User
from crypto.models import Cryptocurrency

class Order(models.Model):
    ORDER_TYPES = [
        ('ask', 'Ask'),
        ('bid', 'Bid'),
    ]
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('filled', 'Filled'),
        ('cancelled', 'Cancelled')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exchange_orders')
    cryptocurrency = models.ForeignKey(Cryptocurrency, on_delete=models.CASCADE, related_name='exchange_orders')
    order_type = models.CharField(max_length=10, choices=ORDER_TYPES)
    price = models.DecimalField(max_digits=20, decimal_places=8)
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    filled_amount = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.order_type.upper()} {self.amount} {self.cryptocurrency.symbol} @ £{self.price} ({self.status})"

class Trade(models.Model):
    ask_order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='trades_as_ask')
    bid_order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='trades_as_bid')
    price = models.DecimalField(max_digits=20, decimal_places=8)
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Trade: {self.amount} @ £{self.price}"
