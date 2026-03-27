from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Cryptocurrency(models.Model):
    name = models.CharField(max_length=50)
    symbol = models.CharField(max_length=10, unique=True)
    decimals = models.IntegerField(default=8)
    mining_reward = models.DecimalField(max_digits=20, decimal_places=8)
    initial_difficulty = models.IntegerField()
    current_price = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    price_updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class PriceHistory(models.Model):
    cryptocurrency = models.ForeignKey(
        Cryptocurrency,
        on_delete=models.CASCADE,
        related_name='price_history'
    )
    price = models.DecimalField(max_digits=20, decimal_places=8)
    recorded_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ['recorded_at']

    def __str__(self):
        return f"{self.cryptocurrency.symbol} @ {self.price} on {self.recorded_at}"

class Blockchain(models.Model):
    network = models.ForeignKey(Cryptocurrency, on_delete=models.CASCADE)
    tip_hash = models.CharField(max_length=64, blank=True, null=True)
    height = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.network.symbol} Chain - Height {self.height}"

class Wallet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wallets')
    cryptocurrency = models.ForeignKey(Cryptocurrency, on_delete=models.CASCADE, related_name='wallets')
    address = models.CharField(max_length=100, unique=True)
    private_key = models.CharField(max_length=255)
    type = models.CharField(max_length=50, default='Standard')

    class Meta:
        unique_together = ('user', 'cryptocurrency')

    def __str__(self):
        return self.user.username + " " + self.cryptocurrency.symbol

class Block(models.Model):
    blockchain = models.ForeignKey(Blockchain, on_delete=models.CASCADE, related_name='blocks')
    block_hash = models.CharField(max_length=64, primary_key=True)
    height = models.IntegerField(db_index=True)
    prev_block_hash = models.CharField(max_length=64)
    timestamp = models.DateTimeField(auto_now_add=True)
    nonce = models.IntegerField(default=0)
    block_data = models.JSONField(blank=True, null=True)

    class Meta:
        ordering = ['height']

    def __str__(self):
        return f"Block {self.height} - {self.block_hash[:8]}..."

class Transaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('failed', 'Failed')
    ]
    tx_id = models.CharField(max_length=64, primary_key=True)
    block = models.ForeignKey(Block, on_delete=models.CASCADE, related_name='transactions', null=True, blank=True)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions_created')
    timestamp = models.DateTimeField(auto_now_add=True)
    fee = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    tx_data = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"TX {self.tx_id[:8]}... ({self.status})"

class TxInput(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='inputs')
    prev_tx_id = models.CharField(max_length=64)
    prev_index = models.IntegerField()
    script_sig = models.TextField()

    def __str__(self):
        return f"In: {self.prev_tx_id[:8]}:{self.prev_index}"

class TxOutput(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='outputs')
    index = models.IntegerField()
    value = models.DecimalField(max_digits=20, decimal_places=8)
    script_pubkey = models.CharField(max_length=255)
    is_spent = models.BooleanField(default=False)
    spent_by_input = models.ForeignKey(
        TxInput,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='spent_output'
    )

    def __str__(self):
        return f"Out: {self.value} to {self.script_pubkey[:8]}"