import time
from cryptocurrency import Cryptocurrency, NetworkConfig, Transaction
from client.miner import Miner
from client.wallet import Wallet

def print_balances(app: Cryptocurrency, alice: Wallet, bob: Wallet):
    print(f"Alice balance: {app.get_balance(alice.address)}")
    print(f"Bob balance: {app.get_balance(bob.address)}")
    print()

def main():
    config = NetworkConfig(
        mining_reward=100,
        address_prefix=b'\x05',
        initial_difficulty=1000000
    )
    
    alice = Wallet(config=config)
    alice_miner = Miner(address=alice.address)
    bob = Wallet(config=config)
    bob_miner = Miner(address=bob.address)

    app = Cryptocurrency(config=config, genesis_address=alice.address)
    print(f"Genesis block hash: {app.get_chain()[0].compute_hash()}")
    print_balances(app, alice, bob)

    print("Alice send Bob 50 coins")
    alice_utxos = app.get_utxos(alice.address)
    signed_tx = alice.create_transaction(bob.address, 50, alice_utxos)
    app.add_transaction(signed_tx)
    print("Alice Mining block 1...")
    template1 = app.get_block_template(miner_address=alice.address)
    block1 = alice_miner.mine(template1)
    app.submit_block(block1)
    print(f"Block 1 Hash: {block1.compute_hash()}")
    print_balances(app, alice, bob)
    print("Bob send Alice 50 coins")
    bob_utxos = app.get_utxos(bob.address)
    signed_tx2 = bob.create_transaction(alice.address, 50, bob_utxos)
    app.add_transaction(signed_tx2)
    print("Bob Mining block 2...")
    template2 = app.get_block_template(miner_address=bob.address)
    block2 = bob_miner.mine(template2)
    app.submit_block(block2)
    print(f"Block 2 Hash: {block2.compute_hash()}")

    print_balances(app, alice, bob)
    print(f"Chain length: {len(app.get_chain())} blocks")
    print(f"Is chain valid? {app.is_chain_valid()}")

if __name__ == "__main__":
    main()