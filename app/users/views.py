from django.views.generic import CreateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .forms import CustomSignUpForm

class SignUpView(CreateView):
    form_class = CustomSignUpForm
    success_url = reverse_lazy('users:login')
    template_name = 'users/signup.html'

class AccountOverviewView(LoginRequiredMixin, TemplateView):
    template_name = 'users/account_overview.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.request.user.profile
        holdings = self.request.user.holdings.all().order_by('symbol')
        snapshots = self.request.user.wallet_snapshots.order_by('-created_at')[:5]
        latest_snapshot = snapshots[0] if snapshots else None
        wallet_value = latest_snapshot.total_value if latest_snapshot else profile.balance
        portfolio_value = wallet_value - profile.balance

        context['profile'] = profile
        context['holdings'] = holdings
        context['snapshots'] = snapshots
        context['wallet_value'] = wallet_value
        context['portfolio_value'] = portfolio_value
        return context

