from django.contrib import admin
from .models import Cryptocurrency, Blockchain, Block, Transaction, TxInput, TxOutput, Wallet

# Register your models here.
admin.site.register(Cryptocurrency)
admin.site.register(Blockchain)
admin.site.register(Block)
admin.site.register(Transaction)
admin.site.register(TxInput)
admin.site.register(TxOutput)
admin.site.register(Wallet)
