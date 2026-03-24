from django.views.generic import TemplateView
from django.http import JsonResponse
import json
from .models import Cryptocurrency, Wallet
from .services import get_blockchain, get_all_networks, submit_mined_block

class BlockchainView(TemplateView):
    template_name = 'crypto/blockchain_viewer.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        cryptos = get_all_networks()
        context['cryptocurrencies'] = cryptos
        selected_crypto_symbol = self.request.GET.get('network')
        
        if selected_crypto_symbol:
            active_crypto = cryptos.filter(symbol=selected_crypto_symbol).first()
        else:
            active_crypto = cryptos.first() if cryptos.exists() else None
            
        context['active_crypto'] = active_crypto
        
        if active_crypto:
            blockchain = get_blockchain(active_crypto.symbol)
            if blockchain:
                chain_data = blockchain.to_json()
                context['blocks'] = chain_data.get('chain', [])
            else:
                context['blocks'] = []
        else:
            context['blocks'] = []
            
        return context

def get_blocks_api(request):
    symbol = request.GET.get('network')
    if not symbol:
        return JsonResponse({'error': 'no network given'}, status=400)
    
    blockchain = get_blockchain(symbol)
    if not blockchain:
        return JsonResponse({'error': 'network not found'}, status=400)
    
    return JsonResponse(blockchain.to_json())

class MiningView(TemplateView):
    template_name = 'crypto/mining.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cryptos = get_all_networks()
        context['cryptocurrencies'] = cryptos
        selected_crypto_symbol = self.request.GET.get('network')
        
        if selected_crypto_symbol:
            active_crypto = cryptos.filter(symbol=selected_crypto_symbol).first()
        else:
            active_crypto = cryptos.first() if cryptos.exists() else None
            
        context['active_crypto'] = active_crypto
        return context

def get_mine_template_api(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required'}, status=401)
        
    symbol = request.GET.get('network')
    if not symbol:
        return JsonResponse({'error': 'Network required'}, status=400)
        
    blockchain = get_blockchain(symbol)
    if not blockchain:
        return JsonResponse({'error': 'Network not found'}, status=404)
        
    wallet = Wallet.objects.filter(user=request.user, cryptocurrency__symbol=symbol).first()
    if not wallet:
        return JsonResponse({'error': f'No wallet found for {symbol}.'}, status=400)
        
    block = blockchain.get_block_template(wallet.address)
    return JsonResponse(block.to_json())

def submit_mined_block_api(request):
    try:
        data = json.loads(request.body)
        symbol = data.get('network')
        submit_mined_block(symbol, data.get('block'))
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'error': str(e)})

class TradingView(TemplateView):
    template_name = 'crypto/trading.html'
