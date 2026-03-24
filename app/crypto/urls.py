from django.urls import path
from .views import (
    BlockchainView, MiningView, TradingView, 
    get_blocks_api, get_mine_template_api, submit_mined_block_api
)

app_name = 'crypto'

urlpatterns = [
    path('blockchain/', BlockchainView.as_view(), name='blockchain_viewer'),
    path('api/blocks/', get_blocks_api, name='api_blocks'),
    path('api/mine/template/', get_mine_template_api, name='api_mine_template'),
    path('api/mine/submit/', submit_mined_block_api, name='api_mine_submit'),
    path('mining/', MiningView.as_view(), name='mining'),
    path('trading/', TradingView.as_view(), name='trading'),
]
