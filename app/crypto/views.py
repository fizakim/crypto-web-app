from django.views.generic import TemplateView
from django.http import JsonResponse
from .models import Cryptocurrency
from .services import get_blockchain, get_all_networks

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

class TradingView(TemplateView):
    template_name = 'crypto/trading.html'
