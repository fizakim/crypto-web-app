class TxInput:
    def __init__(self, prev_tx_hash, output_index, signature=b"", public_key=b""):
        self.prev_tx_hash = prev_tx_hash
        self.output_index = output_index
        self.signature = signature
        self.public_key = public_key

    def to_json(self):
        return {
            "prev_tx_hash": self.prev_tx_hash,
            "output_index": self.output_index,
            "signature": self.signature.hex(),
            "public_key": self.public_key.hex()
        }

    def from_json(data):
        return TxInput(
            prev_tx_hash=data["prev_tx_hash"],
            output_index=data["output_index"],
            signature=bytes.fromhex(data.get("signature", "")),
            public_key=bytes.fromhex(data.get("public_key", ""))
        )
