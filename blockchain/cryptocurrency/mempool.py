class Mempool:
    def __init__(self):
        self.transactions = []

    def add_transaction(self, tx, utxo_set):
        utxo_set.verify_transaction(tx)

        mempool_spent_utxos = set()
        for pending_tx in self.transactions:
            for inp in pending_tx.inputs:
                mempool_spent_utxos.add((inp.prev_tx_hash, inp.output_index))

        for inp in tx.inputs:
            if (inp.prev_tx_hash, inp.output_index) in mempool_spent_utxos:
                raise ValueError(f"Transaction double spends UTXO {inp.prev_tx_hash}:{inp.output_index} already in mempool")

        self.transactions.append(tx)

    def get_transactions(self):
        return list(self.transactions)

    def remove_mined_transactions(self, block):
        mined_tx_hashes = {tx.tx_hash for tx in block.transactions}
        
        consumed_utxos = set()
        for tx in block.transactions:
            for inp in tx.inputs:
                consumed_utxos.add((inp.prev_tx_hash, inp.output_index))
                
        new_transactions = []
        for tx in self.transactions:
            if tx.tx_hash in mined_tx_hashes:
                continue
                
            is_stale = False
            for inp in tx.inputs:
                if (inp.prev_tx_hash, inp.output_index) in consumed_utxos:
                    is_stale = True
                    break
                    
            if not is_stale:
                new_transactions.append(tx)
                
        self.transactions = new_transactions
