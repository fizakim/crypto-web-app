from django.urls import path
from .views import ExchangeView, place_order_api, cancel_order_api, order_book_api

app_name = 'exchange'

urlpatterns = [
    path('', ExchangeView.as_view(), name='exchange'),
    path('api/place/', place_order_api, name='api_place_order'),
    path('api/cancel/<int:order_id>/', cancel_order_api, name='api_cancel_order'),
    path('api/orderbook/', order_book_api, name='api_order_book'),
]
