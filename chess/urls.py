from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required

from .views import (login_view, signup_view,
                    home_view, search_results, update_games, manual_change_view, pair_view, help_view,
                    input_results, download_ratings, download_existing_ratings_sheet)

urlpatterns = [
    path('', login_view, name='login'),
    path('signup/', signup_view, name='signup'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('home/', login_required(home_view), name='home'),
        path('update_games/', login_required(update_games), name='update_games'),
    path('manual_change/', login_required(manual_change_view), name='manual_change'),
    path('input_results/', login_required(input_results), name='input_results'),
    path('pair/', login_required(pair_view), name='pair'),
    path('help/', login_required(help_view), name='help'),

    path('download_ratings/', login_required(download_ratings), name='download_ratings'),
    path('download_existing_ratings_sheet/', login_required(download_existing_ratings_sheet), name='download_existing_ratings_sheet'),

    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]