from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required

from .views import login_view, signup_view, home_view, search_results

urlpatterns = [
    path('', login_view, name='login'),
    path('signup/', signup_view, name='signup'),
    path('home/', login_required(home_view), name='home'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('search/', login_required(search_results), name='search'),
]