from django.urls import path
from .views import BlockchainView, MiningView, TradingView

app_name = 'crypto'

urlpatterns = [
    path('blockchain/', BlockchainView.as_view(), name='blockchain_viewer'),
    path('mining/', MiningView.as_view(), name='mining'),
    path('trading/', TradingView.as_view(), name='trading'),
]
