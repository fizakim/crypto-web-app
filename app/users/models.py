from django.conf import settings
from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=10000.00)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class PortfolioHolding(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='holdings')
    symbol = models.CharField(max_length=20)
    blockchain = models.CharField(max_length=30, blank=True)
    amount = models.DecimalField(max_digits=30, decimal_places=10, default=0)

    def __str__(self):
        return f'{self.user.username} - {self.symbol}'

class WalletSnapshot(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet_snapshots')
    total_value = models.DecimalField(max_digits=18, decimal_places=2)
    period_label = models.CharField(max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} - {self.total_value}'

