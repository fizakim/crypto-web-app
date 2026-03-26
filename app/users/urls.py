from django.urls import path
from django.contrib.auth import views as auth_views
from .views import SignUpView, AccountOverviewView

app_name = 'users'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html', redirect_authenticated_user=True, next_page='pages:home'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='pages:home'), name='logout'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('account/', AccountOverviewView.as_view(), name='account_overview'),
]

