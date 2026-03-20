import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Cryptocurrency, Wallet

from blockchain.client.wallet import Wallet as BlockchainWallet
from blockchain.cryptocurrency.config import NetworkConfig


def make_wallet(u, c):
    config = NetworkConfig(
        mining_reward=float(c.mining_reward),
        initial_difficulty=c.initial_difficulty,
    )
    w = BlockchainWallet(config=config)

    Wallet.objects.create(
        user=u,
        cryptocurrency=c,
        address=w.get_address(),
        private_key=w._sk.to_string().hex(),
    )

@receiver(post_save, sender=User)
def new_user_wallets(sender, instance, **kwargs):
    for c in Cryptocurrency.objects.all():
        if not Wallet.objects.filter(user=instance, cryptocurrency=c).exists():
            make_wallet(instance, c)

@receiver(post_save, sender=Cryptocurrency)
def new_crypto_wallets(sender, instance, **kwargs):
    for u in User.objects.all():
        if not Wallet.objects.filter(user=u, cryptocurrency=instance).exists():
            make_wallet(u, instance)
