import time

from .transaction import Transaction
from .utils import sha256_hash


class Block:
    def __init__(self, index, timestamp, transactions, previous_hash, nonce=0, difficulty=4):
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.difficulty = difficulty

    def compute_hash(self):
        header = (
            str(self.index)
            + str(self.timestamp)
            + self.previous_hash
            + str(self.nonce)
            + str(self.difficulty)
            + "".join(tx.tx_hash for tx in self.transactions)
        )
        return sha256_hash(header.encode())

    def to_json(self):
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": [tx.to_json() for tx in self.transactions],
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "difficulty": self.difficulty
        }

    def from_json(data):
        return Block(
            index=data["index"],
            timestamp=data["timestamp"],
            transactions=[Transaction.from_json(tx) for tx in data.get("transactions", [])],
            previous_hash=data["previous_hash"],
            nonce=data.get("nonce", 0),
            difficulty=data["difficulty"]
        )


def create_genesis_block(config=None, transactions=None):
    from .config import NetworkConfig
    config = config or NetworkConfig()
    if transactions is None:
        transactions = []
    block = Block(
        index=0,
        timestamp=0,
        transactions=transactions,
        previous_hash="0",
        difficulty=config.initial_difficulty,
    )
    
    target = (1 << 256) // block.difficulty
    block_hash = block.compute_hash()
    while int(block_hash, 16) > target:
        block.nonce += 1
        block_hash = block.compute_hash()
        
    return block


