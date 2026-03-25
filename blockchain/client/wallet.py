import ecdsa
import hashlib

from blockchain.cryptocurrency.utils import sha256_hash, base58_encode
from blockchain.cryptocurrency.config import NetworkConfig


class Wallet:
    def __init__(self, private_key=None, config=None):
        self.config = config or NetworkConfig()
        if private_key is None:
            self._sk = ecdsa.SigningKey.generate(curve=self.config.curve)
        else:
            self._sk = private_key
        self._vk = self._sk.get_verifying_key()

    def get_address(self):
        s1 = hashlib.sha256(self._vk.to_string()).digest()
        try:
            h = hashlib.new('ripemd160')
        except ValueError:
            h = hashlib.sha256()
        h.update(s1)
        s2 = h.digest()
        s3 = self.config.address_prefix + s2
        checksum = hashlib.sha256(hashlib.sha256(s3).digest()).digest()[:4]
        return base58_encode(s3 + checksum)

    def get_public_key_bytes(self):
        return self._vk.to_string()

    def sign(self, data):
        return self._sk.sign(data)

    def verify_signature(self, public_key_bytes, data, signature, curve=ecdsa.SECP256k1):
        vk = ecdsa.VerifyingKey.from_string(public_key_bytes, curve=curve)
        try:
            vk.verify(signature, data)
            return True
        except ecdsa.BadSignatureError:
            return False

    def create_transaction(self, recipient_address, amount, available_utxos):
        from cryptocurrency.transaction import Transaction
        from cryptocurrency.tx_input import TxInput
        from cryptocurrency.tx_output import TxOutput
        from cryptocurrency.utils import sha256_hash
        import time

        inputs = []
        input_sum = 0
        
        for tx_hash, out_idx, utxo_amount in available_utxos:
            inputs.append(TxInput(tx_hash, out_idx))
            input_sum += utxo_amount
            if input_sum >= amount:
                break
                
        if input_sum < amount:
            raise ValueError(f"Insufficient funds: have {input_sum}, need {amount}")

        outputs = [TxOutput(recipient_address, amount)]
        
        if input_sum > amount:
            outputs.append(TxOutput(self.get_address(), input_sum - amount))

        tx_hash_data = f"{time.time()}_{self.get_address()}_{recipient_address}_{amount}".encode()
        tx = Transaction(sha256_hash(tx_hash_data), inputs, outputs)

        sig_data = tx.signing_data()
        for i in range(len(tx.inputs)):
            sig = self.sign(sig_data)
            tx.add_signature(i, sig, self.get_public_key_bytes())

        return tx
