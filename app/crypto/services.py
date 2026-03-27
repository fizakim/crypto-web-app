import sys
import os
import json
import glob
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from django.db import transaction as db_transaction

from blockchain.cryptocurrency import Blockchain
from blockchain.cryptocurrency.config import NetworkConfig
from blockchain.cryptocurrency.block import Block
from blockchain.cryptocurrency.transaction import Transaction as ChainTransaction

from .models import Cryptocurrency, Wallet, PriceHistory
from .models import Blockchain as BlockchainModel
from .models import Block as BlockModel
from .models import Transaction as TransactionModel

import ecdsa
from blockchain.client.wallet import Wallet as BlockchainWallet

blockchains = {}

CONFIGS_DIR = os.path.join(os.path.dirname(__file__), '..', 'configs')


def _build_config(crypto):
    return NetworkConfig(
        mining_reward=float(crypto.mining_reward),
        initial_difficulty=crypto.initial_difficulty
    )


def _bootstrap_initial_price_history(crypto):
    if not PriceHistory.objects.filter(cryptocurrency=crypto).exists():
        PriceHistory.objects.create(
            cryptocurrency=crypto,
            price=crypto.current_price
        )


def _hydrate_chain_from_db(blockchain_mem, crypto):
    db_chain = (
        BlockModel.objects
        .filter(blockchain__network=crypto)
        .order_by('height')
    )

    if not db_chain.exists():
        return blockchain_mem

    for db_block in db_chain:
        if db_block.height == 0:
            continue

        if not db_block.block_data:
            continue

        block = Block.from_json(db_block.block_data)
        try:
            blockchain_mem.submit_block(block)
        except ValueError as e:
            # Stop hydration if there's an inconsistency
            print(f"Stopping hydration for {crypto.symbol} at block {db_block.height}: {str(e)}")
            break

    # Hydrate pending transactions
    pending_txs = TransactionModel.objects.filter(
        wallet__cryptocurrency=crypto,
        status='pending'
    )
    for db_tx in pending_txs:
        if db_tx.tx_data:
            from blockchain.cryptocurrency import Transaction as BlockchainTransaction
            tx = BlockchainTransaction.from_json(db_tx.tx_data)
            # Only add if unique
            if tx.tx_hash not in [t.tx_hash for t in blockchain_mem.mempool.transactions]:
                try:
                    blockchain_mem.mempool.add_transaction(tx, blockchain_mem.utxo_set)
                except Exception as e:
                    print(f"Skipping pending tx {tx.tx_hash} during hydration: {str(e)}")

    return blockchain_mem


def get_blockchain(symbol):
    crypto = Cryptocurrency.objects.filter(symbol=symbol).first()
    if not crypto:
        return None

    if symbol not in blockchains:
        config = _build_config(crypto)
        blockchain_mem = Blockchain(config=config)
        blockchains[symbol] = _hydrate_chain_from_db(blockchain_mem, crypto)

    return blockchains[symbol]


def get_all_networks():
    return Cryptocurrency.objects.all()


def get_price_history(symbol, limit=30):
    crypto = Cryptocurrency.objects.filter(symbol=symbol).first()
    if not crypto:
        return []

    history = (
        PriceHistory.objects
        .filter(cryptocurrency=crypto)
        .order_by('-recorded_at')[:limit]
    )

    return list(reversed(history))


def get_explorer_blocks(symbol, limit=12):
    crypto = Cryptocurrency.objects.filter(symbol=symbol).first()
    if not crypto:
        return []

    db_blocks = (
        BlockModel.objects
        .filter(blockchain__network=crypto)
        .order_by('-height')[:limit]
    )

    blocks = []
    for db_block in reversed(list(db_blocks)):
        if db_block.block_data:
            raw = db_block.block_data
            blocks.append({
                'index': raw.get('index', db_block.height),
                'timestamp': raw.get('timestamp'),
                'block_hash': raw.get('block_hash', db_block.block_hash),
                'previous_hash': raw.get('previous_hash', db_block.prev_block_hash),
                'nonce': raw.get('nonce', db_block.nonce),
                'difficulty': raw.get('difficulty', crypto.initial_difficulty),
                'transactions': raw.get('transactions', []),
                'tx_count': len(raw.get('transactions', [])),
            })
        else:
            blocks.append({
                'index': db_block.height,
                'timestamp': int(db_block.timestamp.timestamp()),
                'block_hash': db_block.block_hash,
                'previous_hash': db_block.prev_block_hash,
                'nonce': db_block.nonce,
                'difficulty': crypto.initial_difficulty,
                'transactions': [],
                'tx_count': 0,
            })

    return blocks


def get_chain_snapshot(symbol):
    crypto = Cryptocurrency.objects.filter(symbol=symbol).first()
    if not crypto:
        return {'difficulty': 0, 'chain': []}

    blocks = get_explorer_blocks(symbol, limit=1000)
    blockchain_mem = get_blockchain(symbol)

    return {
        'difficulty': blockchain_mem.difficulty if blockchain_mem else crypto.initial_difficulty,
        'chain': blocks,
    }


def init_network(crypto):
    config = _build_config(crypto)
    chain = Blockchain(config=config)
    blockchains[crypto.symbol] = chain

    blockchain_record = BlockchainModel.objects.filter(network=crypto).first()
    if blockchain_record:
        _bootstrap_initial_price_history(crypto)
        _hydrate_chain_from_db(chain, crypto)
        return

    genesis = chain.chain[0]
    genesis_hash = genesis.compute_hash()

    with db_transaction.atomic():
        blockchain_record = BlockchainModel.objects.create(
            network=crypto,
            tip_hash=genesis_hash,
            height=0,
        )

        BlockModel.objects.create(
            blockchain=blockchain_record,
            block_hash=genesis_hash,
            height=0,
            prev_block_hash=genesis.previous_hash,
            nonce=genesis.nonce,
            block_data=genesis.to_json(),
        )

    _bootstrap_initial_price_history(crypto)


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
    if not blockchain_mem:
        raise ValueError("Network not found")

    if not isinstance(block_data, dict):
        raise ValueError("Invalid block payload")

    submitted_transactions = block_data.get("transactions", [])
    if not isinstance(submitted_transactions, list) or len(submitted_transactions) == 0:
        raise ValueError("Block must include transactions")

    mempool_by_hash = {tx.tx_hash: tx for tx in blockchain_mem.mempool.get_transactions()}
    resolved_transactions = []
    seen_hashes = set()

    # Resolve transactions from mempool to ensure data integrity
    for tx_index, tx_data in enumerate(submitted_transactions):
        tx_hash = tx_data.get("tx_hash") if isinstance(tx_data, dict) else None
        if not tx_hash:
            raise ValueError("Submitted transaction missing tx_hash")

        if tx_index == 0:
            coinbase_tx = ChainTransaction.from_json(tx_data)
            if not coinbase_tx.is_coinbase():
                raise ValueError("First block transaction must be coinbase")
            resolved_transactions.append(coinbase_tx)
            continue

        if tx_hash in seen_hashes:
            raise ValueError(f"Duplicate transaction in block: {tx_hash}")
        seen_hashes.add(tx_hash)

        mempool_tx = mempool_by_hash.get(tx_hash)
        if mempool_tx is None:
            raise ValueError(f"Submitted transaction not found in mempool: {tx_hash}")
        resolved_transactions.append(mempool_tx)

    block = Block(
        index=block_data["index"],
        timestamp=block_data["timestamp"],
        transactions=resolved_transactions,
        previous_hash=block_data["previous_hash"],
        nonce=block_data.get("nonce", 0),
        difficulty=block_data["difficulty"],
    )
    blockchain_mem.submit_block(block)

    crypto = Cryptocurrency.objects.get(symbol=symbol)
    blockchain_record = BlockchainModel.objects.get(network=crypto)
    block_hash = block.compute_hash()

    with db_transaction.atomic():
        # Update or create block record
        db_block, created = BlockModel.objects.update_or_create(
            blockchain=blockchain_record,
            height=block.index,
            defaults={
                'block_hash': block_hash,
                'prev_block_hash': block.previous_hash,
                'nonce': block.nonce,
                'block_data': block.to_json()
            }
        )

        blockchain_record.tip_hash = block_hash
        blockchain_record.height = block.index
        blockchain_record.save(update_fields=['tip_hash', 'height'])

        # Update transaction statuses
        db_block = BlockModel.objects.get(block_hash=block_hash)
        for tx in block.transactions:
            TransactionModel.objects.filter(tx_id=tx.tx_hash).update(
                status='confirmed',
                block=db_block
            )

    return True


def get_mempool_transactions():
    pass


def get_user_crypto_balance(user, symbol):
    wallet = Wallet.objects.filter(user=user, cryptocurrency__symbol=symbol).first()
    if not wallet:
        return Decimal('0')

    blockchain = get_blockchain(symbol)
    if not blockchain:
        return Decimal('0')

    return Decimal(str(blockchain.get_balance(wallet.address)))


def submit_transfer(user, symbol, recipient_address, amount_str):
    amount = float(amount_str)
    
    wallet_record = Wallet.objects.filter(user=user, cryptocurrency__symbol=symbol).first()
    if not wallet_record:
        raise ValueError(f"No wallet found for {symbol}.")
        
    crypto = Cryptocurrency.objects.filter(symbol=symbol).first()
    if not crypto:
        raise ValueError("Network not found.")
        
    config = _build_config(crypto)
    sk = ecdsa.SigningKey.from_string(bytes.fromhex(wallet_record.private_key), curve=ecdsa.SECP256k1)
    b_wallet = BlockchainWallet(private_key=sk, config=config)
    
    blockchain_mem = get_blockchain(symbol)
    if not blockchain_mem:
        raise ValueError("Network not running.")
        
    sender_address = b_wallet.get_address()
    if sender_address == recipient_address:
        raise ValueError("Cannot send coins to yourself.")
        
    utxos = []
    for tx_hash, out_idx, utxo in blockchain_mem.utxo_set.get_utxos_for_address(sender_address):
        utxos.append((tx_hash, out_idx, utxo.amount))
    signed_tx = b_wallet.create_transaction(recipient_address, amount, utxos)
    
    blockchain_mem.add_transaction(signed_tx)
    
    # Persist transaction to DB
    TransactionModel.objects.create(
        tx_id=signed_tx.tx_hash,
        wallet=wallet_record,
        status='pending',
        tx_data=signed_tx.to_json()
    )
    
    return True
