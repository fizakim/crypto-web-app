import time
from .block import Block, create_genesis_block
from .utxo_set import UTXOSet
from .mempool import Mempool
from .transaction import Transaction
from .tx_output import TxOutput
from .utils import sha256_hash
from .config import NetworkConfig

class Blockchain:
    def __init__(self, config=None, genesis_address=None):
        self.config = config or NetworkConfig()
        self.difficulty = self.config.initial_difficulty
        self.utxo_set = UTXOSet(config=self.config)
        self.mempool = Mempool()

        genesis_transactions = []
        if genesis_address:
            tx = Transaction(
                tx_hash="tx1",
                inputs=[],
                outputs=[TxOutput(genesis_address, 100)]
            )
            genesis_transactions.append(tx)

        self.chain = [create_genesis_block(config=self.config, transactions=genesis_transactions)]

        for tx in genesis_transactions:
            self.utxo_set.apply_transaction(tx)

    def to_json(self):
        return {
            "difficulty": self.difficulty,
            "chain": [block.to_json() for block in self.chain]
        }

    def adjust_difficulty(self):
        return self.difficulty

    def get_last_block(self):
        return self.chain[-1]

    def add_transaction(self, transaction):
        self.mempool.add_transaction(transaction, self.utxo_set)

    def get_block_template(self, miner_address=None):
        if miner_address is None:
            raise ValueError("Miner address is required to receive the mining reward")

        transactions_to_mine = self.mempool.get_transactions()

        total_fees = 0
        for tx in transactions_to_mine:
            input_sum = 0
            for inp in tx.inputs:
                utxo = self.utxo_set.get(inp.prev_tx_hash, inp.output_index)
                if utxo:
                    input_sum += utxo.amount
            output_sum = sum(out.amount for out in tx.outputs)
            total_fees += (input_sum - output_sum)

        reward_tx_hash = sha256_hash(f"coinbase_{int(time.time())}_{miner_address}".encode())
        reward_tx = Transaction(
            tx_hash=reward_tx_hash,
            inputs=[],
            outputs=[TxOutput(miner_address, self.config.mining_reward + total_fees)]
        )

        transactions_to_mine.insert(0, reward_tx)

        last_block = self.get_last_block()
        
        # self.adjust_difficulty()
        
        new_block = Block(
            index=last_block.index + 1,
            timestamp=int(time.time()),
            transactions=transactions_to_mine,
            previous_hash=last_block.compute_hash(),
            difficulty=self.difficulty
        )
        
        return new_block

    def submit_block(self, block):
        target = (1 << 256) // block.difficulty
        if int(block.compute_hash(), 16) > target:
            raise ValueError("Block hash does not meet difficulty target")
            
        last_block = self.get_last_block()
        if block.previous_hash != last_block.compute_hash():
            raise ValueError("Block previous hash does not match current chain tip")

        for tx in block.transactions:
            self.utxo_set.apply_transaction(tx)
            
        self.chain.append(block)
        self.mempool.remove_mined_transactions(block)
        
        return block

    def is_chain_valid(self):
        verification_utxo_set = UTXOSet(config=self.config)

        for i in range(len(self.chain)):
            current = self.chain[i]

            target = (1 << 256) // current.difficulty
            if int(current.compute_hash(), 16) > target:
                print(f"Validation failed: Block {i} hash does not meet difficulty target.")
                return False
                
            if i > 0:
                previous = self.chain[i - 1]
                if current.previous_hash != previous.compute_hash():
                    print(f"Validation failed: Block {i} previous hash does not match Block {i-1}.")
                    return False
                    
            try:
                for tx in current.transactions:
                    verification_utxo_set.apply_transaction(tx)
            except ValueError as e:
                print(f"Validation failed at Block {i}: {e}")
                return False
                
        return True
