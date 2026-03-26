from django.contrib import admin
from .models import UserProfile, PortfolioHolding, WalletSnapshot

admin.site.register(UserProfile)
admin.site.register(PortfolioHolding)
admin.site.register(WalletSnapshot)