from decimal import Decimal
from django.db import transaction
from .models import Order, Trade
from crypto.services import get_user_crypto_balance

def get_order_book(symbol):
    asks = Order.objects.filter(cryptocurrency__symbol=symbol, order_type='ask', status='open').order_by('price')
    bids = Order.objects.filter(cryptocurrency__symbol=symbol, order_type='bid', status='open').order_by('-price')
    
    from crypto.models import Cryptocurrency
    crypto = Cryptocurrency.objects.get(symbol=symbol)
    
    return {
        'current_price': float(crypto.current_price),
        'asks': [
            {'id': a.id, 'user': a.user.username, 'price': float(a.price), 'amount': float(a.amount - a.filled_amount)} for a in asks
        ],
        'bids': [
            {'id': b.id, 'user': b.user.username, 'price': float(b.price), 'amount': float(b.amount - b.filled_amount)} for b in bids
        ]
    }

def place_order(user, crypto, order_type, price, amount):
    price = Decimal(str(price))
    amount = Decimal(str(amount))

    with transaction.atomic():
        if order_type == 'bid':
            total_cost = price * amount
            if Decimal(str(user.profile.balance)) < total_cost:
                raise ValueError("Insufficient balance")
        else: # ask
            crypto_balance = Decimal(str(get_user_crypto_balance(user, crypto.symbol)))
            open_ask_amount = sum(o.amount - o.filled_amount for o in Order.objects.filter(user=user, cryptocurrency=crypto, order_type='ask', status='open'))
            available_balance = crypto_balance - open_ask_amount
            
            if available_balance < amount:
                raise ValueError(f"Insufficient locked balance. Available: {available_balance}")

        order = Order.objects.create(
            user=user,
            cryptocurrency=crypto,
            order_type=order_type,
            price=price,
            amount=amount
        )
        
        match_orders(order)
        return order


def match_orders(new_order):
    if new_order.status != 'open':
        return

    expected_type = 'ask' if new_order.order_type == 'bid' else 'bid'
    
    matches = Order.objects.filter(
        cryptocurrency=new_order.cryptocurrency,
        order_type=expected_type,
        status='open'
    )

    if new_order.order_type == 'bid':
        matches = matches.filter(price__lte=new_order.price).order_by('price', 'created_at')
    else:
        matches = matches.filter(price__gte=new_order.price).order_by('-price', 'created_at')

    remaining_amount = new_order.amount - new_order.filled_amount

    for match in matches:
        if remaining_amount <= 0:
            break

        match_remaining = match.amount - match.filled_amount
        fill_amount = min(remaining_amount, match_remaining)
        exec_price = match.price

        Trade.objects.create(
            ask_order=match if expected_type == 'ask' else new_order,
            bid_order=new_order if new_order.order_type == 'bid' else match,
            price=exec_price,
            amount=fill_amount
        )

        new_order.cryptocurrency.current_price = exec_price
        new_order.cryptocurrency.save()

        match.filled_amount += fill_amount
        if match.filled_amount == match.amount:
            match.status = 'filled'
        match.save()

        new_order.filled_amount += fill_amount
        remaining_amount -= fill_amount

        ask_user = match.user if expected_type == 'ask' else new_order.user
        bid_user = new_order.user if new_order.order_type == 'bid' else match.user

        total_cost = exec_price * fill_amount
        
        bid_balance = Decimal(str(bid_user.profile.balance))
        ask_balance = Decimal(str(ask_user.profile.balance))
        
        bid_user.profile.balance = bid_balance - total_cost
        ask_user.profile.balance = ask_balance + total_cost
        
        bid_user.profile.save()
        ask_user.profile.save()

    if new_order.filled_amount == new_order.amount:
        new_order.status = 'filled'
    new_order.save()


def cancel_order(user, order_id):
    order = Order.objects.get(id=order_id, user=user)
    if order.status == 'open':
        order.status = 'cancelled'
        order.save()
        return True
    return False
