from django.urls import path
from .views import BlockchainView, MiningView, TradingView, get_blocks_api

app_name = 'crypto'

urlpatterns = [
    path('blockchain/', BlockchainView.as_view(), name='blockchain_viewer'),
    path('api/blocks/', get_blocks_api, name='api_blocks'),
    path('mining/', MiningView.as_view(), name='mining'),
    path('trading/', TradingView.as_view(), name='trading'),
]
