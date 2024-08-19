from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .forms import SignUpForm
from .models import RegisteredUser

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"You are now logged in as {username}.")
                return redirect('home')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'chess/login.html', {'form': form, 'title': 'Login'})


def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            if user:
                login(request, user)
                return redirect('home')
    else:
        form = SignUpForm()

    return render(request, 'chess/signup.html', {'form': form})


def home_view(request):
    if request.user.is_authenticated:
        return render(request, 'chess/home.html', {'username': request.user.username})
    else:
        return redirect('login')


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            RegisteredUser.objects.create(user=user)
            return redirect('login')  # Adjust the redirect as needed
    else:
        form = UserCreationForm()
    return render(request, 'chess/signup.html', {'form': form})

@login_required
def profile(request):
    registered_user = RegisteredUser.objects.get(user=request.user)
    return render(request, 'chess/home.html', {'registered_user': registered_user})