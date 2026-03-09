from .tx_output import TxOutput
from .transaction import Transaction
import ecdsa
from .config import NetworkConfig

class UTXOSet:
    def __init__(self, config=None):
        self.config = config or NetworkConfig()
        self._utxos = {}
        self._addr_index = {}

    def _key(self, tx_hash, index):
        return f"{tx_hash}:{index}"

    def add(self, tx_hash, index, output):
        key = self._key(tx_hash, index)
        if key in self._utxos:
            raise ValueError(f"UTXO {key} already exists")
        self._utxos[key] = output
        self._addr_index.setdefault(output.recipient_address, set()).add(key)

    def remove(self, tx_hash, index):
        key = self._key(tx_hash, index)
        output = self._utxos.pop(key, None)
        if output is None:
            raise KeyError(f"UTXO {key} not found")
        addr_set = self._addr_index.get(output.recipient_address)
        if addr_set is not None:
            addr_set.discard(key)
            if not addr_set:
                del self._addr_index[output.recipient_address]
        return output

    def get(self, tx_hash, index):
        return self._utxos.get(self._key(tx_hash, index))

    def get_balance(self, address):
        keys = self._addr_index.get(address, set())
        return sum(self._utxos[k].amount for k in keys)

    def get_utxos_for_address(self, address):
        results = []
        for key in self._addr_index.get(address, set()):
            tx_hash, idx = key.rsplit(":", 1)
            results.append((tx_hash, int(idx), self._utxos[key]))
        return results

    def verify_transaction(self, tx):
        if tx.is_coinbase():
            return

        data = tx.signing_data()
        total_input_value = 0

        for inp in tx.inputs:
            utxo = self.get(inp.prev_tx_hash, inp.output_index)
            if utxo is None:
                raise ValueError(f"UTXO {inp.prev_tx_hash}:{inp.output_index} not found")

            vk = ecdsa.VerifyingKey.from_string(inp.public_key, curve=self.config.curve)
            import hashlib
            from .utils import base58_encode
            s1 = hashlib.sha256(vk.to_string()).digest()
            try:
                h = hashlib.new('ripemd160')
            except ValueError:
                h = hashlib.sha256()
            h.update(s1)
            s2 = h.digest()
            s3 = self.config.address_prefix + s2
            checksum = hashlib.sha256(hashlib.sha256(s3).digest()).digest()[:4]
            expected_addr = base58_encode(s3 + checksum)
            
            if expected_addr != utxo.recipient_address:
                raise ValueError("Public key does not match UTXO owner")

            try:
                vk.verify(inp.signature, data)
            except ecdsa.BadSignatureError:
                raise ValueError(f"Invalid signature for input {inp.prev_tx_hash}:{inp.output_index}")
            
            total_input_value += utxo.amount

        total_output_value = sum(out.amount for out in tx.outputs)
        if total_input_value < total_output_value:
            raise ValueError(f"Transaction outputs ({total_output_value}) exceed inputs ({total_input_value})")

    def apply_transaction(self, tx):
        self.verify_transaction(tx)

        removed = []
        added = []

        try:
            for inp in tx.inputs:
                output = self.remove(inp.prev_tx_hash, inp.output_index)
                removed.append((inp.prev_tx_hash, inp.output_index, output))

            for idx, out in enumerate(tx.outputs):
                self.add(tx.tx_hash, idx, out)
                added.append((tx.tx_hash, idx))

        except (KeyError, ValueError):
            for tx_hash, index in added:
                try:
                    self.remove(tx_hash, index)
                except KeyError:
                    pass
            for tx_hash, index, output in removed:
                try:
                    self.add(tx_hash, index, output)
                except ValueError:
                    pass
            raise

    def __len__(self):
        return len(self._utxos)

    def __repr__(self):
        return f"UTXOSet({len(self)} utxos)"
