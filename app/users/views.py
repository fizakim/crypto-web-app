from django.views.generic import CreateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .forms import CustomSignUpForm

from crypto.models import Wallet
from crypto.services import get_user_crypto_balance


class SignUpView(CreateView):
    form_class = CustomSignUpForm
    success_url = reverse_lazy('users:login')
    template_name = 'users/signup.html'

class AccountOverviewView(LoginRequiredMixin, TemplateView):
    template_name = 'users/account_overview.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        profile = user.profile
        latest_snapshot = user.wallet_snapshots.order_by('-created_at').first()
        wallet_value = latest_snapshot.total_value if latest_snapshot else profile.balance

        # Wallet data for every cryptocurrency the user has a wallet for
        wallets = Wallet.objects.filter(user=user).select_related('cryptocurrency')
        wallet_list = []
        for w in wallets:
            balance = get_user_crypto_balance(user, w.cryptocurrency.symbol)
            wallet_list.append({
                'name': w.cryptocurrency.name,
                'symbol': w.cryptocurrency.symbol,
                'address': w.address,
                'private_key': w.private_key,
                'balance': balance,
            })

        context['profile'] = profile
        context['wallet_value'] = wallet_value
        context['wallet_list'] = wallet_list
        context['member_since'] = user.date_joined
        return context
