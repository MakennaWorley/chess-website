from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required

from .views import (login_view, signup_view,
                    home_view, search_results, manual_change_view, input_results_view, pair_view, help_view)

urlpatterns = [
    path('', login_view, name='login'),
    path('signup/', signup_view, name='signup'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('home/', login_required(home_view), name='home'),
    path('search/', login_required(search_results), name='search'),
    path('manual_change/', login_required(manual_change_view), name='manual_change'),
    path('input_results/', login_required(input_results_view), name='input_results'),
    path('pair/', login_required(pair_view), name='pair'),
    path('help/', login_required(help_view), name='help'),

    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]