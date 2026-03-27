from django.urls import path
from .views import (
    BlockchainView, MiningView, TransferView, 
    get_blocks_api, get_mine_template_api, submit_mined_block_api,
    get_wallet_info_api, transfer_coins_api, get_explorer_state_api
)

app_name = 'crypto'

urlpatterns = [
    path('blockchain/', BlockchainView.as_view(), name='blockchain_viewer'),
    path('api/blocks/', get_blocks_api, name='api_blocks'),
    path('api/mine/template/', get_mine_template_api, name='api_mine_template'),
    path('api/mine/submit/', submit_mined_block_api, name='api_mine_submit'),
    path('mining/', MiningView.as_view(), name='mining'),
    path('transfer/', TransferView.as_view(), name='transfer'),
    path('api/wallet/info/', get_wallet_info_api, name='api_wallet_info'),
    path('api/transfer/', transfer_coins_api, name='api_transfer'),
    path('api/explorer-state/', get_explorer_state_api, name='api_explorer_state'),
]
