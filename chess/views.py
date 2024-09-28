from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.db.models import Count, Q
from django.db.models.functions import TruncWeek
from django.http import HttpResponseRedirect, HttpResponse, FileResponse
from django.shortcuts import render, redirect

from .forms import SignUpForm, SearchForm
from .models import RegisteredUser, Player, LessonClass, Game #, Club
from .write_to_file import write_ratings


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
    if request.user.is_authenticated:
        registered_user = RegisteredUser.objects.get(user=request.user)
        '''if registered_user.club:
            club_name = registered_user.club
        else:
            club_name = None  # or some default value if the user is not associated with any club'''

        players = Player.objects.filter(is_active=True, is_volunteer=False).order_by('-rating')[:10]
        class_list = LessonClass.objects.filter(is_active=True)
        games = (
            Game.objects
            .filter(is_active=True)  # Only active games
            .annotate(week=TruncWeek('date_of_match'))  # Group by week
            .values('week')  # Select the week
            .annotate(game_count=Count('id'))  # Count the number of games per week
            .order_by('-week')  # Order by week in descending order
        )

        return render(request, 'chess/home.html', {
            'username': request.user.username,
            #'club_name': club_name,
            'players': players,
            'class_list': class_list,
            'games': games,
        })
    else:
        return redirect('login/', )


def help_view(request):
    return render(request, 'chess/help.html', )


def manual_change_view(request):
    return render(request, 'chess/manual_change.html', )

def input_results_view(request):
    return render(request, 'chess/input_results.html', )

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

            #print(query)

            if len(query) >= 2 and query[0].isalpha() and query[1:].isdigit():
                letter = query[0].upper()
                number = int(query[1:])
            elif len(query) >= 2 and query[-1].isalpha() and query[:-1].isdigit():
                letter = query[-1].upper()
                number = int(query[:-1])
            else:
                return render(request, 'chess/search.html', {
                    'form': form,
                    'results': ["Unable to find board " + query],
                })

            game_results = Game.objects.filter(
                Q(board_letter=letter) & Q(board_number=number) & Q(is_active=True)
            )
            results.extend(game_results)

        #searching a player
        elif search_type == 'Player':
            player_results = Player.objects.filter(
                Q(first_name__icontains=query) & Q(is_active=True) | Q(last_name__icontains=query) & Q(is_active=True)
            ).order_by('-rating', '-grade', 'last_name', 'first_name')
            results.extend(player_results)

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


def download_ratings(request):
    file_path = write_ratings()

    with open(file_path, 'rb') as excel_file:
        response = HttpResponse(excel_file.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="ratings.xlsx"'
        return response