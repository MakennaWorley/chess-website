from django.urls import path

from .views import login_view, signup_view, home_view

urlpatterns = [
    path('', login_view, name='login'),
    path('signup/', signup_view, name='signup'),
    path('home/', home_view, name='home'),
]