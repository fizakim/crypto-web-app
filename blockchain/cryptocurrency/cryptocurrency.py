from .blockchain import Blockchain
from .config import NetworkConfig
from .transaction import Transaction

class Cryptocurrency:
    def __init__(self, config=None, genesis_address=None):
        self.config = config or NetworkConfig()
        self.blockchain = Blockchain(config=self.config, genesis_address=genesis_address)

    def get_balance(self, address):
        return self.blockchain.utxo_set.get_balance(address)

    def get_utxos(self, address):
        available = []
        for tx_hash, out_idx, utxo in self.blockchain.utxo_set.get_utxos_for_address(address):
            available.append((tx_hash, out_idx, utxo.amount))
        return available

    def add_transaction(self, tx):
        self.blockchain.add_transaction(tx)

    def get_block_template(self, miner_address):
        return self.blockchain.get_block_template(miner_address=miner_address)

    def submit_block(self, block):
        return self.blockchain.submit_block(block)
    
    def get_chain(self):
        return self.blockchain.chain

    def is_chain_valid(self):
        return self.blockchain.is_chain_valid()
