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

        # setup the very first block
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
        # helper to convert chain to something we can send over json
        return {
            "difficulty" : self.difficulty, # difficulty level
            "chain": [block.to_json() for block in self.chain]
        }

    def adjust_difficulty(self):
        # for now just keep it static
        return self.difficulty

    def get_last_block(self):
        # helper to get the tip of the chain
        return self.chain[-1]

    def get_balance(self, address):
        return self.utxo_set.get_balance(address)

    def add_transaction(self, transaction):
        self.mempool.add_transaction(transaction, self.utxo_set)

    def get_block_template(self, miner_address=None):
        if not miner_address:
            raise ValueError("Need a miner address for the reward!!")

        to_mine = []
        fees = 0
        
        # go through the mempool and pick out valid transactions
        for tx in self.mempool.get_transactions():
            try:
                self.utxo_set.verify_transaction(tx)
                
                # prevent double spending
                input_sum = 0
                for inp in tx.inputs:
                    utxo = self.utxo_set.get(inp.prev_tx_hash, inp.output_index)
                    input_sum += utxo.amount
                    
                output_sum = sum(out.amount for out in tx.outputs)
                fees += (input_sum - output_sum)
                to_mine.append(tx)
            except Exception:
                # ignore bad ones
                continue

        last_block = self.get_last_block()
        next_idx = last_block.index + 1
        
        # make the coinbase transaction for the miner
        reward_hash = sha256_hash(f"coinbase_{next_idx}_{int(time.time())}_{miner_address}".encode())
        reward_tx = Transaction(
            tx_hash=reward_hash,
            inputs=[],
            outputs=[TxOutput(miner_address, self.config.mining_reward + fees)]
        )

        to_mine.insert(0, reward_tx)

        new_block = Block(
            index=next_idx,
            timestamp=int(time.time()),
            transactions=to_mine,
            previous_hash=last_block.compute_hash(),
            difficulty=self.difficulty
        )
        
        return new_block

    def submit_block(self, block):
        # check if they actually did the proof of work
        target = (1 << 256) // block.difficulty
        if int(block.compute_hash(), 16) > target:
            raise ValueError("Hash is too high, work not done")
            
        last_block = self.get_last_block()
        if block.previous_hash != last_block.compute_hash():
            raise ValueError("Previous hash doesn't match the tip")

        # update the utxos with the new transactions
        for tx in block.transactions:
            self.utxo_set.apply_transaction(tx)
            
        self.chain.append(block)
        # clean up the mempool
        self.mempool.remove_mined_transactions(block)
        
        return block

    def is_chain_valid(self):
        # build a temporary utxo set to verify everything from scratch
        verify_utxos = UTXOSet(config=self.config)

        for i in range(len(self.chain)):
            current = self.chain[i]

            target = (1 << 256) // current.difficulty
            if int(current.compute_hash(), 16) > target:
                print(f"FAILED: Block {i} hash is wrong.")
                return False
                
            if i > 0:
                previous = self.chain[i - 1]
                if current.previous_hash != previous.compute_hash():
                    print(f"FAILED: Block {i} prev hash mismatch.")
                    return False
                    
            try:
                for tx in current.transactions:
                    verify_utxos.apply_transaction(tx)
            except ValueError as e:
                print(f"FAILED at Block {i}: {e}")
                return False
                
        return True
