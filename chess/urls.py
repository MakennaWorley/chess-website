from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required

from .views import (login_view, signup_view,
                    home_view, search_results, update_games, get_ratings_sheet,
                    manual_change_view,
                    input_results_view, get_players, save_games, download_ratings, download_existing_ratings_sheet,
                    pair_view, new_pairings, download_pairings,
                    help_view, )

urlpatterns = [
    path('', login_view, name='login'),
    path('signup/', signup_view, name='signup'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('home/', login_required(home_view), name='home'),
        path('api/get_ratings_sheet', login_required(get_ratings_sheet), name='get_ratings_sheet'),
        path('update_games/', login_required(update_games), name='update_games'),
    path('manual_change/', login_required(manual_change_view), name='manual_change'),
    path('input_results/', login_required(input_results_view), name='input_results'),
        path('api/players/', login_required(get_players), name='get_players'),
        path('save_games/', login_required(save_games), name='save_games'),
        path('download_ratings/', login_required(download_ratings), name='download_ratings'),
        path('download_existing_ratings_sheet/', login_required(download_existing_ratings_sheet), name='download_existing_ratings_sheet'),
    path('pair/', login_required(pair_view), name='pair'),
        path('new_pairings/', login_required(new_pairings), name='new_pairings'),
        path('download_pairings/', login_required(download_pairings), name='download_pairings'),
    path('help/', login_required(help_view), name='help'),

    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]