from django.urls import path
from .views import (
    ExchangeView, 
    place_order_api, 
    cancel_order_api, 
    order_book_api,
    get_exchange_user_data_api
)

app_name = 'exchange'

urlpatterns = [
    path('', ExchangeView.as_view(), name='exchange'),
    path('api/place/', place_order_api, name='api_place_order'),
    path('api/cancel/<int:order_id>/', cancel_order_api, name='api_cancel_order'),
    path('api/orderbook/', order_book_api, name='api_order_book'),
    path('api/user-data/', get_exchange_user_data_api, name='api_user_data'),
]
