class TxOutput:
    def __init__(self, recipient_address, amount):
        self.recipient_address = recipient_address
        self.amount = amount

    def to_json(self):
        return {
            "recipient_address": self.recipient_address,
            "amount": self.amount
        }

    def from_json(data):
        return TxOutput(
            recipient_address=data["recipient_address"],
            amount=data["amount"]
        )
