import json

from .tx_input import TxInput
from .tx_output import TxOutput


class Transaction:
    def __init__(self, tx_hash, inputs=None, outputs=None):
        self.tx_hash = tx_hash
        self.inputs = inputs if inputs is not None else []
        self.outputs = outputs if outputs is not None else []

    def is_coinbase(self):
        return len(self.inputs) == 0

    def signing_data(self):
        data = {
            "tx_hash": self.tx_hash,
            "inputs": [{"prev_tx_hash": inp.prev_tx_hash, "output_index": inp.output_index} for inp in self.inputs],
            "outputs": [{"recipient_address": out.recipient_address, "amount": out.amount} for out in self.outputs]
        }
        return json.dumps(data, separators=(',', ':'), sort_keys=True).encode('utf-8')

    def to_json(self):
        return {
            "tx_hash": self.tx_hash,
            "inputs": [inp.to_json() for inp in self.inputs],
            "outputs": [out.to_json() for out in self.outputs]
        }

    def from_json(data):
        return Transaction(
            tx_hash=data["tx_hash"],
            inputs=[TxInput.from_json(inp) for inp in data.get("inputs", [])],
            outputs=[TxOutput.from_json(out) for out in data.get("outputs", [])]
        )

    def add_signature(self, input_index, signature, public_key):
        if 0 <= input_index < len(self.inputs):
            inp = self.inputs[input_index]
            self.inputs[input_index] = TxInput(
                prev_tx_hash=inp.prev_tx_hash,
                output_index=inp.output_index,
                signature=signature,
                public_key=public_key
            )
        else:
            raise IndexError("Input index out of range")
