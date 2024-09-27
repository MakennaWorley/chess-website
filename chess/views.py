from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import path
from .forms import SignUpForm, SearchForm
from .models import RegisteredUser, Player, LessonClass, Game #, Club
#from .decorators import redirect_if_authenticated


#@redirect_if_authenticated
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next')
                if next_url:
                    return HttpResponseRedirect(next_url)
                else:
                    return redirect('home')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'chess/login.html', {'form': form})


#@redirect_if_authenticated
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
        return redirect('login/', {'title': 'Login'})


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


def search_results(request):
    form = SearchForm(request.GET or None)
    results = []

    if form.is_valid():
        query = form.cleaned_data['query']
        search_type = form.cleaned_data['search_board']
        selected_models = form.cleaned_data['models']

        #searching a board
        if search_type == 'Board':
            letter = ''
            number = -1

            if len(query) >= 2 and query[0].isalpha() and query[1:].isdigit():
                letter = query[0]
                number = int(query[1:])
            elif len(query) >= 2 and query[-1].isalpha() and query[:-1].isdigit():
                letter = query[-1]
                number = int(query[:-1])
            else:
                return render(request, 'chess/search.html', {
                    'form': form,
                    'results': ["Unable to find board " + query],
                })

            game_results = Game.objects.filter(
                Q(board_letter=letter) & Q(board_number=number)
            )
            results.extend(game_results)

        #searching a player
        elif search_type == 'Player':
            if 'Player' in selected_models or 'All' in selected_models:
                player_results = Player.objects.filter(
                    Q(first_name__icontains=query) | Q(last_name__icontains=query)
                )
                results.extend(player_results)

            if 'LessonClass' in selected_models or 'All' in selected_models:
                lesson_results = LessonClass.objects.filter(
                    Q(teacher__first_name__icontains=query) |
                    Q(teacher__last_name__icontains=query) |
                    Q(co_teacher__first_name__icontains=query) |
                    Q(co_teacher__last_name__icontains=query)
                )
                results.extend(lesson_results)

            if 'Game' in selected_models or 'All' in selected_models:
                game_results = Game.objects.filter(
                    Q(white__first_name__icontains=query) |
                    Q(white__last_name__icontains=query) |
                    Q(black__first_name__icontains=query) |
                    Q(black__last_name__icontains=query)
                )
                results.extend(game_results)

        else:
            players = Player.objects.filter(
                Q(lesson_class__teacher__first_name__icontains=query) |
                Q(lesson_class__co_teacher__first_name__icontains=query)
            )
            results.extend(players)

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