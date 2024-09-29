import os
import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.db.models import Q, Count
from django.http import HttpResponseRedirect, HttpResponse, Http404, JsonResponse
from django.shortcuts import render, redirect

from .forms import SignUpForm, SearchForm
from .models import RegisteredUser, Player, LessonClass, Game #, Club
from .write_to_file import write_ratings


GAME_SORT_ORDER = ['G', 'H', 'I', 'J']
CREATED_FILES_DIR = os.path.join(os.path.dirname(__file__), '../files', 'ratings')


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


def home_view(request):
    games_by_date = Game.objects.filter(is_active=True).values('date_of_match').annotate(game_count=Count('id')).order_by('-date_of_match')

    players = Player.objects.filter(active_member=True, is_active=True, is_volunteer=False).order_by('-rating')
    class_list = LessonClass.objects.filter(is_active=True)

    context = {
        'players': players,
        'class_list': class_list,
        'games_by_date': games_by_date,
    }

    return render(request, 'chess/home.html', context)


def update_games(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        game_date = data.get('game_date')

        print(game_date)

        #games = Game.objects.filter(date_of_match=game_date) if game_type == 'by_date' else Game.objects.all()

        if game_date:
            games = Game.objects.filter(date_of_match=game_date)
        else:
            games = []

        game_list = [
            {
                'board': game.get_board(),
                'white': game.white.name() if game.white else 'N/A',
                'black': game.black.name() if game.black else 'N/A',
                'result': game.result
            }
            for game in games
        ]

        return JsonResponse({'games': game_list})

    return JsonResponse({'error': 'Invalid request'}, status=400)


def help_view(request):
    return render(request, 'chess/help.html', )


def manual_change_view(request):
    return render(request, 'chess/manual_change.html', )

def pair_view(request):
    return render(request, 'chess/pair.html', )


def search_results(request):
    form = SearchForm(request.GET or None)
    results = []

    if form.is_valid():
        query = form.cleaned_data['query']
        search_type = form.cleaned_data['search_board']

        #searching a board
        if search_type == 'Board':
            letter = ''
            number = -1

            if len(query) >= 2 and query[0].isalpha() and query[1:].isdigit():
                letter = query[0].upper()
                number = int(query[1:])
            elif len(query) >= 2 and query[-1].isalpha() and query[:-1].isdigit():
                letter = query[-1].upper()
                number = int(query[:-1])

            game_results = Game.objects.filter(
                Q(board_letter=letter) & Q(board_number=number) & Q(is_active=True)
            ).order_by('-date_of_match')
            results.extend(game_results)

        #searching a player
        elif search_type == 'Player':
            player_results = Player.objects.filter(
                Q(first_name__icontains=query) & Q(is_active=True) & Q(active_member=True) |
                Q(last_name__icontains=query) & Q(is_active=True) & Q(active_member=True)
            ).order_by('-rating', '-grade', 'last_name', 'first_name')
            results.extend(player_results)

        #search in a class
        else:
            players = Player.objects.filter(
                Q(lesson_class__teacher__first_name__icontains=query) & Q(is_active=True) |
                Q(lesson_class__co_teacher__first_name__icontains=query) & Q(is_active=True)
            ).order_by('-rating', '-grade', 'last_name', 'first_name')
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


def input_results(request):
    ratings_dir = os.path.join(settings.BASE_DIR, 'files', 'ratings')
    try:
        existing_files = os.listdir(ratings_dir)
    except FileNotFoundError:
        existing_files = []

    if ".DS_Store" in existing_files:
        existing_files.remove(".DS_Store")

    context = {'existing_files': existing_files}
    return render(request, 'chess/input_results.html', context)


def download_existing_ratings_sheet(request):
    file_name = request.GET.get('file')
    if file_name:
        file_path = os.path.join(CREATED_FILES_DIR, file_name)
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/octet-stream')
                response['Content-Disposition'] = f'attachment; filename="{file_name}"'
                return response
        else:
            raise Http404("File does not exist")
    return redirect('input_results')


def download_ratings(request):
    file_path = write_ratings()

    with open(file_path, 'rb') as excel_file:
        response = HttpResponse(excel_file.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="ratings.xlsx"'
        return response