from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.validators import RegexValidator

from .forms import SignUpForm, SearchForm
from .models import RegisteredUser, Player, LessonClass, Game #, Club


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

    return render(request, 'chess/signup.html', {'form': form, 'title': 'Sign Up'})


def home_view(request):
    if request.user.is_authenticated:
        registered_user = RegisteredUser.objects.get(user=request.user)
        '''if registered_user.club:
            club_name = registered_user.club
        else:
            club_name = None  # or some default value if the user is not associated with any club'''

        players = Player.objects.all()
        class_list = LessonClass.objects.all()
        games = Game.objects.all()

        return render(request, 'chess/home.html', {
            'username': request.user.username,
            #'club_name': club_name,
            'players': players,
            'class_list': class_list,
            'games': games,
        })
    else:
        return redirect('login', {'title': 'Login'})


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


def search_results(request):
    form = SearchForm(request.GET or None)
    results = []

    if form.is_valid():
        query = form.cleaned_data['query']
        selected_models = form.cleaned_data['models']

        #searching a board

        #searching a player
        if 'Player' in selected_models or 'All' in selected_models:
            player_results = Player.objects.filter(name__icontains=query)
            results.extend(player_results)

        if 'LessonClass' in selected_models or 'All' in selected_models:
            lesson_results = LessonClass.objects.filter(
                Q(teacher__name__icontains=query) | Q(co_teacher__name__icontains=query)
            )
            results.extend(lesson_results)

        if 'Game' in selected_models or 'All' in selected_models:
            game_results = Game.objects.filter(
                Q(white__name__icontains=query) |
                Q(black__name__icontains=query)
            )
            results.extend(game_results)

    if not results:
        return render(request, 'chess/search.html', {
            'form': form,
            'results': ["No results found"],
        })

    context = {
        'form': form,
        'results': results
    }
    return render(request, 'chess/search.html', context)