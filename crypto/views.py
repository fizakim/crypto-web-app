from django.views.generic import TemplateView

class BlockchainView(TemplateView):
    template_name = 'crypto/blockchain_viewer.html'

class MiningView(TemplateView):
    template_name = 'crypto/mining.html'

class TradingView(TemplateView):
    template_name = 'crypto/trading.html'
