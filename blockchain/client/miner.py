from cryptocurrency.block import Block

class Miner:
    def __init__(self, address):
        self.address = address

    def mine(self, block_template):
        target = (1 << 256) // block_template.difficulty
        
        block_hash = block_template.compute_hash()
        while int(block_hash, 16) > target:
            block_template.nonce += 1
            block_hash = block_template.compute_hash()
            
        return block_template
