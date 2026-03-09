import ecdsa

class NetworkConfig:
    def __init__(self, 
                 mining_reward=50.0,
                 block_generation_interval=10,
                 difficulty_adjustment_interval=10,
                 address_prefix=b'\x00',
                 curve=ecdsa.SECP256k1,
                 initial_difficulty=1000):
        self.mining_reward = mining_reward
        self.block_generation_interval = block_generation_interval
        self.difficulty_adjustment_interval = difficulty_adjustment_interval
        self.address_prefix = address_prefix
        self.curve = curve
        self.initial_difficulty = initial_difficulty
