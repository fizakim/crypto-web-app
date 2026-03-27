import json
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from crypto.services import get_all_networks, get_user_crypto_balance
from .models import Order
from .services import get_order_book, place_order, cancel_order

class ExchangeView(TemplateView):
    template_name = 'exchange/exchange.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cryptos = get_all_networks()
        context['cryptocurrencies'] = cryptos
        # see which crypto the user has selected from the dropdown
        selected_crypto = self.request.GET.get('network')
        
        if selected_crypto:
            active_crypto = cryptos.filter(symbol=selected_crypto).first()
        else:
            # default to first one if nothing selected
            active_crypto = cryptos.first() if cryptos.exists() else None
            
        context['active_crypto'] = active_crypto
        
        if self.request.user.is_authenticated:
            if active_crypto:
                context['crypto_balance'] = get_user_crypto_balance(self.request.user, active_crypto.symbol)
            else:
                context['crypto_balance'] = 0
                
            # list open orders so the user can cancel them
            context['open_orders'] = Order.objects.filter(
                user=self.request.user, 
                status='open'
            ).order_by('-created_at')
            
        return context

def place_order_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required'}, status=401)
        
    try:
        data = json.loads(request.body)
        symbol = data.get('network')
        order_type = data.get('order_type')
        price = data.get('price')
        amount = data.get('amount')
        
        # make sure we have all the data we need
        if not symbol:
            return JsonResponse({'error': 'Missing network'}, status=400)
        if not order_type:
            return JsonResponse({'error': 'Missing order type'}, status=400)
        if not price:
            return JsonResponse({'error': 'Missing price'}, status=400)
        if not amount:
            return JsonResponse({'error': 'Missing amount'}, status=400)
            
        from crypto.models import Cryptocurrency
        crypto = Cryptocurrency.objects.get(symbol=symbol)
        
        order = place_order(request.user, crypto, order_type, price, amount)
        
        return JsonResponse({
            'status': 'success', 
            'order_id': order.id,
            'filled_amount': str(order.filled_amount),
            'order_status': order.status
        })
    except Exception as e:
        # something went wrong
        return JsonResponse({'error': str(e)}, status=400)

def cancel_order_api(request, order_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required'}, status=401)
        
    success = cancel_order(request.user, order_id)
    if success:
        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'error': 'Failed to cancel order'}, status=400)

def order_book_api(request):
    symbol = request.GET.get('network')
    if not symbol:
        return JsonResponse({'error': 'no network given'}, status=400)
        
    book = get_order_book(symbol)
    return JsonResponse(book)

def get_exchange_user_data_api(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required'}, status=401)
        
    symbol = request.GET.get('network')
    if not symbol:
        return JsonResponse({'error': 'Network required'}, status=400)
        
    from crypto.models import Cryptocurrency
    crypto = Cryptocurrency.objects.filter(symbol=symbol).first()
    
    crypto_balance = 0
    if crypto:
        crypto_balance = get_user_crypto_balance(request.user, symbol)
        
    open_orders = Order.objects.filter(
        user=request.user, 
        cryptocurrency=crypto,
        status='open'
    ).order_by('-created_at')
    
    orders_data = []
    for o in open_orders:
        orders_data.append({
            'id': o.id,
            'order_type': o.order_type,
            'price': float(o.price),
            'amount': float(o.amount),
            'filled_amount': float(o.filled_amount),
            'created_at': o.created_at.strftime('%b %d, %H:%M:%S')
        })
        
    return JsonResponse({
        'fiat_balance': float(request.user.profile.balance),
        'crypto_balance': float(crypto_balance),
        'open_orders': orders_data
    })
