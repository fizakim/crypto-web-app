import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from blockchain.cryptocurrency import Blockchain
from blockchain.cryptocurrency.config import NetworkConfig
from .models import Cryptocurrency

blockchains = {}

def get_blockchain(symbol):
    if symbol not in blockchains:
        crypto = Cryptocurrency.objects.filter(symbol=symbol).first()
        if not crypto:
            return None
        
        config = NetworkConfig(
            mining_reward=float(crypto.mining_reward),
            initial_difficulty=crypto.initial_difficulty
        )
        blockchains[symbol] = Blockchain(config=config)
    
    return blockchains[symbol]

def get_all_networks():
    return Cryptocurrency.objects.all()

def start_mining_operation(user, node_address):
    pass

def get_mempool_transactions():
    pass
