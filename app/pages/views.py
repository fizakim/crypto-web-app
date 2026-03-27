from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from crypto.models import Cryptocurrency


@login_required(login_url='users:login')
def home(request):
    selected_period = request.GET.get('period', '7d')
    allowed_periods = {'24h', '7d', '30d', 'all'}
    if selected_period not in allowed_periods:
        selected_period = '7d'

    period_labels = {
        '24h': '24 Hours',
        '7d': '7 Days',
        '30d': '30 Days',
        'all': 'All Time',
    }

    profile = request.user.profile
    holdings = request.user.holdings.all()

    if selected_period == '24h':
        snapshots = request.user.wallet_snapshots.order_by('-created_at')[:24]
    elif selected_period == '7d':
        snapshots = request.user.wallet_snapshots.order_by('-created_at')[:7]
    elif selected_period == '30d':
        snapshots = request.user.wallet_snapshots.order_by('-created_at')[:30]
    elif selected_period == 'all':
        snapshots = request.user.wallet_snapshots.order_by('-created_at')
    else:
        snapshots = request.user.wallet_snapshots.order_by('-created_at')[:7]

    snapshots = list(snapshots)[::-1]

    wallet_value = snapshots[-1].total_value if snapshots else profile.balance
    cash_balance = profile.balance
    investment_earnings = wallet_value - cash_balance

    wallet_change_percent = 0
    if len(snapshots) >= 2:
        earlier_value = snapshots[0].total_value
        latest_value = snapshots[-1].total_value
        if earlier_value != 0:
            wallet_change_percent = ((latest_value - earlier_value) / earlier_value) * 100

    all_cryptos = Cryptocurrency.objects.all()
    
    # Enrich cryptos with holdings
    enriched_holdings = []
    for crypto in all_cryptos:
        holding = request.user.holdings.filter(symbol=crypto.symbol).first()
        amount = holding.amount if holding else 0
        enriched_holdings.append({
            'symbol': crypto.symbol,
            'name': crypto.name,
            'amount': amount,
            'price': crypto.current_price,
            'value_gbp': float(amount) * float(crypto.current_price)
        })

    chart_labels = [snapshot.period_label for snapshot in snapshots]
    chart_values = [float(snapshot.total_value) for snapshot in snapshots]

    if not chart_labels:
        chart_labels = [period_labels[selected_period]]
        chart_values = [float(wallet_value)]

    context = {
        'wallet_value': wallet_value,
        'cash_balance': cash_balance,
        'investment_earnings': investment_earnings,
        'wallet_change_percent': round(wallet_change_percent, 2),
        'holdings': enriched_holdings,
        'chart_labels': chart_labels,
        'chart_values': chart_values,
        'selected_period': selected_period,
        'selected_period_label': period_labels[selected_period],
    }

    return render(request, 'pages/home.html', context)
