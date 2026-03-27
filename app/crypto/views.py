from django.views.generic import TemplateView
from django.http import JsonResponse
import json

from .models import Wallet, Transaction
from .services import (
    get_blockchain,
    get_all_networks,
    get_chain_snapshot,
    get_price_history,
    submit_mined_block,
    get_user_crypto_balance,
    submit_transfer
)


class BlockchainView(TemplateView):
    template_name = 'crypto/blockchain_viewer.html'

    def _build_explorer_context(self, active_crypto, blocks, price_history, blockchain_mem):
        if not active_crypto:
            return {
                'stats': {},
                'recent_blocks': [],
                'price_chart_labels': [],
                'price_chart_values': [],
            }

        latest_block = blocks[-1] if blocks else None
        total_transactions = sum(len(block.get('transactions', [])) for block in blocks)

        stats = {
            'symbol': active_crypto.symbol,
            'name': active_crypto.name,
            'height': latest_block.get('index', 0) if latest_block else 0,
            'difficulty': latest_block.get('difficulty', active_crypto.initial_difficulty) if latest_block else active_crypto.initial_difficulty,
            'reward': active_crypto.mining_reward,
            'price': active_crypto.current_price,
            'latest_hash': latest_block.get('block_hash', '') if latest_block else '',
            'latest_timestamp': latest_block.get('timestamp', '') if latest_block else '',
            'total_blocks': len(blocks),
            'total_transactions': total_transactions,
            'utxo_count': len(blockchain_mem.utxo_set) if blockchain_mem else 0,
        }

        price_chart_labels = [
            point.recorded_at.strftime('%d %b %H:%M')
            for point in price_history
        ]
        price_chart_values = [
            float(point.price)
            for point in price_history
        ]

        return {
            'stats': stats,
            'recent_blocks': list(reversed(blocks[-12:])),
            'price_chart_labels': price_chart_labels,
            'price_chart_values': price_chart_values,
        }

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

        blocks = []
        price_history = []
        blockchain_mem = None

        if active_crypto:
            blockchain_mem = get_blockchain(active_crypto.symbol)
            chain_snapshot = get_chain_snapshot(active_crypto.symbol)
            blocks = chain_snapshot.get('chain', [])
            price_history = get_price_history(active_crypto.symbol, limit=30)

        context['blocks'] = blocks
        
        # Add pending transactions
        if active_crypto:
            pending_txs = Transaction.objects.filter(
                wallet__cryptocurrency=active_crypto,
                status='pending'
            ).order_by('-timestamp')
            context['pending_transactions'] = pending_txs

        context.update(self._build_explorer_context(active_crypto, blocks, price_history, blockchain_mem))
        return context


def get_blocks_api(request):
    symbol = request.GET.get('network')
    if not symbol:
        return JsonResponse({'error': 'no network given'}, status=400)

    blockchain = get_blockchain(symbol)
    if not blockchain:
        return JsonResponse({'error': 'network not found'}, status=400)

    chain_snapshot = get_chain_snapshot(symbol)
    return JsonResponse(chain_snapshot)


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
        return JsonResponse({'error': str(e)}, status=400)


class TradingView(TemplateView):
    template_name = 'crypto/trading.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cryptocurrencies'] = get_all_networks()
        
        # Add pending transactions for the user
        if self.request.user.is_authenticated:
            pending_txs = Transaction.objects.filter(
                wallet__user=self.request.user,
                status='pending'
            ).order_by('-timestamp')
            context['pending_transactions'] = pending_txs
            
        return context


def get_wallet_info_api(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required'}, status=401)
        
    symbol = request.GET.get('network')
    if not symbol:
        return JsonResponse({'error': 'Network required'}, status=400)
        
    wallet = Wallet.objects.filter(user=request.user, cryptocurrency__symbol=symbol).first()
    if not wallet:
        return JsonResponse({'error': f'No wallet found for {symbol}.'}, status=400)
        
    balance = get_user_crypto_balance(request.user, symbol)
    
    return JsonResponse({
        'address': wallet.address,
        'balance': str(balance)
    })


def transfer_coins_api(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
        
    try:
        data = json.loads(request.body)
        symbol = data.get('network')
        recipient_address = data.get('recipient_address')
        amount = data.get('amount')
        
        if not all([symbol, recipient_address, amount]):
            return JsonResponse({'error': 'Missing fields'}, status=400)
            
        submit_transfer(request.user, symbol, recipient_address, amount)
        return JsonResponse({'status': 'success'})
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': f"Failed to transfer: {str(e)}"}, status=400)