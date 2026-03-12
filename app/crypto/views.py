from django.views.generic import TemplateView
from .models import Cryptocurrency, Block

class BlockchainView(TemplateView):
    template_name = 'crypto/blockchain_viewer.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        cryptos = Cryptocurrency.objects.all()
        context['cryptocurrencies'] = cryptos
        selected_crypto_symbol = self.request.GET.get('network')
        
        if selected_crypto_symbol:
            active_crypto = Cryptocurrency.objects.filter(symbol=selected_crypto_symbol).first()
        else:
            active_crypto = cryptos.first() if cryptos.exists() else None
            
        context['active_crypto'] = active_crypto
        
        if active_crypto:
            blockchain = active_crypto.blockchain_set.first()
            if blockchain:
                blocks = Block.objects.filter(blockchain=blockchain).order_by('-height')[:50] # Get latest 50 blocks
                context['blocks'] = blocks
            else:
                context['blocks'] = []
        else:
            context['blocks'] = []
            
        return context

class MiningView(TemplateView):
    template_name = 'crypto/mining.html'

class TradingView(TemplateView):
    template_name = 'crypto/trading.html'
