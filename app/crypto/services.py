import sys
import os
import json
import glob

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from django.db import transaction as db_transaction

from blockchain.cryptocurrency import Blockchain
from blockchain.cryptocurrency.config import NetworkConfig
from .models import Cryptocurrency
from .models import Blockchain as BlockchainModel
from .models import Block as BlockModel
from blockchain.cryptocurrency.block import Block

blockchains = {}

CONFIGS_DIR = os.path.join(os.path.dirname(__file__), '..', 'configs')


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


def init_network(crypto):
    config = NetworkConfig(
        mining_reward=float(crypto.mining_reward),
        initial_difficulty=crypto.initial_difficulty,
    )
    chain = Blockchain(config=config)
    blockchains[crypto.symbol] = chain

    if not BlockchainModel.objects.filter(network=crypto).exists():
        genesis = chain.chain[0]
        genesis_hash = genesis.compute_hash()

        with db_transaction.atomic():
            blockchain_record = BlockchainModel.objects.create(
                network=crypto,
                tip_hash=genesis_hash,
                height=1,
            )

            BlockModel.objects.create(
                blockchain=blockchain_record,
                block_hash=genesis_hash,
                height=0,
                prev_block_hash=genesis.previous_hash,
                nonce=genesis.nonce,
            )


def load_configs():
    if not os.path.isdir(CONFIGS_DIR):
        print("configs directory not found")
        return
    for f in glob.glob(os.path.join(CONFIGS_DIR, '*.json')):
        with open(f, 'r') as file:
            data = json.load(file)

        crypto, is_new = Cryptocurrency.objects.update_or_create(
            symbol=data['symbol'],
            defaults={
                'name': data['name'],
                'decimals': data.get('decimals', 8),
                'mining_reward': data['mining_reward'],
                'initial_difficulty': data['initial_difficulty'],
            },
        )

        init_network(crypto)

        if is_new:
            print(f"added new crypto {crypto.symbol}")
        else:
            print(f"loaded {crypto.symbol}")


def start_mining_operation(user, node_address):
    pass

def submit_mined_block(symbol, block_data):
    blockchain_mem = get_blockchain(symbol)
        
    block = Block.from_json(block_data)
    blockchain_mem.submit_block(block)
    
    crypto = Cryptocurrency.objects.get(symbol=symbol)
    blockchain_record = BlockchainModel.objects.get(network=crypto)
    
    # Save to database (student style, no transaction.atomic)
    BlockModel.objects.create(
        blockchain=blockchain_record,
        block_hash=block.compute_hash(),
        height=block.index,
        prev_block_hash=block.previous_hash,
        nonce=block.nonce,
        block_data=block_data
    )
    
    blockchain_record.tip_hash = block.compute_hash()
    blockchain_record.height = block.index
    blockchain_record.save()
        
    return True


def get_mempool_transactions():
    pass
