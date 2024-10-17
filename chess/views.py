import os
import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q, Count
from django.http import HttpResponseRedirect, HttpResponse, Http404, JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone

from .forms import SignUpForm, SearchForm, PairingDateForm, GameSaveForm
from .models import RegisteredUser, Player, LessonClass, Game  # , Club
from .write_to_file import write_ratings, write_pairings

CREATED_RATING_FILES_DIR = os.path.join(os.path.dirname(__file__), '../files', 'ratings')
CREATED_PAIRING_FILES_DIR = os.path.join(os.path.dirname(__file__), '../files', 'pairings')

BOARD_SORT_ORDER = ['G', 'H', 'I', 'J']
BOARDS = [
    *[f"G-{i + 1}" for i in range(5)],
    *[f"H-{i + 1}" for i in range(6)],
    *[f"I-{i + 1}" for i in range(22)],
    *[f"J-{i + 1}" for i in range(22)]
]

RATINGS_HELPER = lambda rating, result, expected: round(rating + 32 * (result - expected))
CALC_EXPECTED = lambda player_rating, opponent_rating: 1 / (1 + 10 ** ((opponent_rating - player_rating) / 400))


def get_players(request):
    players = Player.objects.filter(active_member=True, is_active=True).order_by('last_name', 'first_name')

    players_data = [
        {
            "id": player.id,
            "first_name": player.first_name,
            "last_name": player.last_name
        }
        for player in players
    ]

    return JsonResponse({'players': players_data})


def get_ratings_sheet(request):
    players = Player.objects.filter(active_member=True, is_active=True, is_volunteer=False).order_by('-rating',
                                                                                                     '-grade',
                                                                                                     'last_name',
                                                                                                     'first_name')
    return render(request, 'chess/ratings_sheet.html', {'players': players})


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
    games_by_date = Game.objects.filter(is_active=True).values('date_of_match').annotate(
        game_count=Count('id')).order_by('-date_of_match')

    players = Player.objects.filter(active_member=True, is_active=True, is_volunteer=False).order_by('-rating',
                                                                                                     '-grade',
                                                                                                     'last_name',
                                                                                                     'first_name')
    class_list = LessonClass.objects.filter(is_active=True)

    context = {
        'players': players,
        'class_list': class_list,
        'games_by_date': games_by_date,
    }

    return render(request, 'chess/home.html', context)


def update_games(request):
    if request.method == 'POST':
        try:
            # Parse the request body for the selected game date
            body = json.loads(request.body)
            game_date = body.get('game_date')

            # Explicitly fetch the latest games for the selected date, bypassing any queryset caching
            games = Game.objects.filter(date_of_match=game_date, is_active=True).all()

            # Prepare game data for the response
            games_data = []
            for game in games:
                if game.result == 'NONE' or game.result == 'U':
                    result = ''
                else:
                    result = game.result

                games_data.append({
                    'board': game.get_board(),
                    'white': game.white.name() if game.white else 'N/A',
                    'black': game.black.name() if game.black else 'N/A',
                    'result': result
                })

            # Return the game data as JSON response
            return JsonResponse({'games': games_data}, status=200)

        except Exception as e:
            # Return an error response in case of any issues
            return JsonResponse({'error': str(e)}, status=400)

            # Return an error response if the request is not a POST request
        return JsonResponse({'error': 'Invalid request method.'}, status=405)


def manual_change_view(request):
    return render(request, 'chess/manual_change.html', )


def input_results_view(request):
    form = GameSaveForm()

    games_by_date = Game.objects.filter(is_active=True).values('date_of_match').annotate(
        game_count=Count('id')).order_by('-date_of_match')

    ratings_dir = os.path.join(settings.BASE_DIR, 'files', 'ratings')
    try:
        existing_files = os.listdir(ratings_dir)
    except FileNotFoundError:
        existing_files = []

    if ".DS_Store" in existing_files:
        existing_files.remove(".DS_Store")

    existing_files = sorted(
        existing_files,
        key=lambda f: os.path.getmtime(os.path.join(ratings_dir, f)),
        reverse=True
    )

    context = {
        'form': form,
        'games_by_date': games_by_date,
        'existing_files': existing_files
    }
    return render(request, 'chess/input_results.html', context)


def save_games(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            game_date = data.get('game_date')
            games = data.get('games')

            if not games:
                return JsonResponse({'status': 'error', 'message': 'No games data received'}, status=400)

            games_keyed = {
                game['board']: {key: value for key, value in game.items() if key != 'board'} for game in games
                if not (game['white'] == "N/A" and game['black'] == "N/A")
            }
            # print(games_keyed)

            games_db = Game.objects.filter(date_of_match=game_date)
            games_db_keyed = {
                game.get_board(): game for game in games_db
            }
            # print(games_db_keyed)

            # games not in the db
            new_games_to_db = {
                board: details for board, details in games_keyed.items() if board not in games_db_keyed
            }
            print("Games being added:", new_games_to_db)

            # games not in data
            games_not_in_data = {
                board: game for board, game in games_db_keyed.items() if board not in games_keyed
            }
            print("Games being deactivated:", games_not_in_data)

            updated_games = {}

            for board, details in games_keyed.items():
                if board in games_db_keyed:
                    db_game = games_db_keyed[board]

                    white_db = db_game.white.name() if db_game.white is not None else "N/A"
                    black_db = db_game.black.name() if db_game.black is not None else "N/A"
                    result_db = db_game.result or "NONE"

                    '''if details['white'] == "N/A" or details['black'] == "N/A":
                        print(board, "is not going to be updated with a result")'''

                    if white_db != details['white'] or black_db != details['black'] or result_db != details['result']:
                        updated_games[board] = details
            print("Games being updated:", updated_games)

            # Prepare results messages
            added_games_report = []
            deactivated_games_report = []
            updated_games_report = []

            # Dictionary of Boards that will have both players getting a ratings change
            games_with_results = {}

            user = request.user

            with transaction.atomic():
                # Add new games
                for board, details in new_games_to_db.items():
                    try:
                        white_player = Player.objects.get(first_name=details['white'].split(', ')[1],
                                                          last_name=details['white'].split(', ')[0]) if details[
                                                                                                            'white'] != "N/A" else None
                        black_player = Player.objects.get(first_name=details['black'].split(', ')[1],
                                                          last_name=details['black'].split(', ')[0]) if details[
                                                                                                            'black'] != "N/A" else None
                        if details['result'] != "NONE":
                            games_with_results[board] = [white_player, black_player, details['result']]
                        Game.add_game(
                            date_of_match=game_date,
                            board_letter=board[0],
                            board_number=int(board[2:]),
                            white=white_player,
                            black=black_player,
                            result=details['result'],
                            modified_by=user
                        )
                        added_games_report.append(f"Added game for board {board}")
                    except ValidationError as e:
                        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

                # Deactivate games
                for board, game in games_not_in_data.items():
                    game.is_active = False
                    game.end_at = timezone.now()
                    game.save()
                    deactivated_games_report.append(f"Deactivated game for board {board}")

                # Update existing games
                for board, details in updated_games.items():
                    db_game = games_db_keyed[board]
                    white_player = Player.objects.filter(first_name=details['white'].split(', ')[1],
                                                         last_name=details['white'].split(', ')[0],
                                                         is_active=True).first() if details[
                                                                                        'white'] != "N/A" else None
                    black_player = Player.objects.filter(first_name=details['black'].split(', ')[1],
                                                         last_name=details['black'].split(', ')[0],
                                                         is_active=True).first() if details[
                                                                                        'black'] != "N/A" else None
                    if details['result'] != "NONE":
                        games_with_results[board] = [white_player, black_player, details['result']]

                    db_game.update_game(
                        date_of_match=game_date,
                        board_letter=board[0],
                        board_number=int(board[2:]),
                        white=white_player,
                        black=black_player,
                        result=details['result'],
                        modified_by=user
                    )
                    updated_games_report.append(f"Updated game for board {board}")

            # Prepare the final response
            response_data = {
                'status': 'success',
                'message': 'Games processed successfully',
                'added_games': added_games_report,
                'deactivated_games': deactivated_games_report,
                'updated_games': updated_games_report
            }

            print(games_with_results)
            players = []

            with transaction.atomic():
                for game, details in games_with_results.items():
                    '''white.append(details[0]) # these are player objects
                    black.append(details[1])
                    results.append(details[2])'''

                    if details[0] in Player.objects.filter(is_active=True, is_volunteer=True).all() or details[
                        1] in Player.objects.filter(is_active=True, is_volunteer=True).all():
                        print("Game has a volunteer playing")
                        continue

                    else:
                        if details[2] == 'White':
                            w_rating = RATINGS_HELPER(details[0].rating, 1,
                                                      CALC_EXPECTED(details[0].rating, details[1].rating))
                            b_rating = RATINGS_HELPER(details[1].rating, 0,
                                                      CALC_EXPECTED(details[1].rating, details[0].rating))
                        elif details[2] == 'Draw':
                            w_rating = RATINGS_HELPER(details[0].rating, .5,
                                                      CALC_EXPECTED(details[0].rating, details[1].rating))
                            b_rating = RATINGS_HELPER(details[1].rating, .5,
                                                      CALC_EXPECTED(details[1].rating, details[0].rating))
                        else:
                            w_rating = RATINGS_HELPER(details[0].rating, 0,
                                                      CALC_EXPECTED(details[0].rating, details[1].rating))
                            b_rating = RATINGS_HELPER(details[1].rating, 1,
                                                      CALC_EXPECTED(details[1].rating, details[0].rating))
                        # Add player's new rating
                        Player.update_rating(details[0], w_rating, details[1], user)
                        Player.update_rating(details[1], b_rating, details[0], user)

                    players.append(f"{details[0].last_name}, {details[0].first_name}")
                    players.append(f"{details[1].last_name}, {details[1].first_name}")

            response_data['ratings'] = players

            return JsonResponse(response_data, status=200)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


def download_existing_ratings_sheet(request):
    file_name = request.GET.get('file')
    if file_name:
        file_path = os.path.join(CREATED_RATING_FILES_DIR, file_name)
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
        response = HttpResponse(excel_file.read(),
                                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
        return response


def pair_view(request):
    form = PairingDateForm()  # Create an instance of the form
    return render(request, 'chess/pair.html', {'form': form})


def new_pairings(request):
    if request.method == 'POST':
        try:
            unicode = request.body.decode('utf-8')
            data = json.loads(unicode)

            game_date = data.get('game_date')
            games = data.get('games')
            separate_classes = data.get('separate_classes', False)

            print(game_date, separate_classes)

            used_boards = []
            paired_players = set()

            user = request.user

            # Manually created games
            with transaction.atomic():
                for game in games:
                    board = game.get('board')
                    white_player_name = game.get('whitePlayer')
                    black_player_name = game.get('blackPlayer')
                    print(board, white_player_name, black_player_name)

                    white_player = Player.objects.filter(first_name=white_player_name.split(', ')[1],
                                                         last_name=white_player_name.split(', ')[0],
                                                         is_active=True).first()
                    black_player = Player.objects.filter(first_name=black_player_name.split(', ')[1],
                                                         last_name=black_player_name.split(', ')[0],
                                                         is_active=True).first()

                    used_boards.append(board)
                    paired_players.add(white_player)
                    paired_players.add(black_player)
                    print(white_player.name, black_player.name)

                    Game.add_game(
                        date_of_match=game_date,
                        board_letter=board[0],
                        board_number=int(board[2:]),
                        white=white_player,
                        black=black_player,
                        result='',
                        modified_by=user
                    )

            message = "All manual pairings were successfully created."
            unused_boards = [board for board in BOARDS if board not in used_boards]
            unpaired_players = list(Player.objects.filter(is_active=True, is_volunteer=False).exclude(
                id__in=[player.id for player in paired_players]).order_by('-rating', '-grade', 'last_name',
                                                                          'first_name'))

            print(unused_boards, unpaired_players)
            print(pair_players(unpaired_players, separate_classes))

            return JsonResponse({'status': 'success', 'message': message}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


def pair_players(players, separate_classes):
    # players: list of Player objects with ratings
    # separate_classes_flag: whether to separate Krishnam and Sam's classes

    pairings = []
    unpaired = []

    if separate_classes:
        krishnam_class = [p for p in players if p.lesson_class.name == 'Krishnam']
        sam_class = [p for p in players if p.lesson_class.name == 'Sam']
        other_class = [p for p in players if p.lesson_class.name not in ['Krishnam', 'Sam']]
    else:
        krishnam_class = []
        sam_class = []
        other_class = players

    print(krishnam_class)
    print(sam_class)
    print(other_class)

    # if separate_classes:
    #     pair_within_class(pairings, krishnam_class)
    #     pair_within_class(pairings, sam_class)
    pair_within_class(pairings, unpaired, other_class)

    return pairings, unpaired


def pair_within_class(pairings, unpaired, class_players):

    for player in class_players:
        print(f"Trying to pair {player.first_name} {player.last_name}")
        if player.opponent_one:
            potential_opponents = [p for p in class_players if p != player
                                   and abs(player.rating - p.rating) <= 20
                                   and p not in [player.opponent_one, player.opponent_two, player.opponent_three]]

            print(
                f"Potential opponents for {player.first_name} {player.last_name}: {[p.first_name + ' ' + p.last_name for p in potential_opponents]}")
            print(potential_opponents)

            if potential_opponents:
                print("Checking first potential opponent", potential_opponents[0])
                opponent = potential_opponents[0]
                last_game_player = get_last_game(player)
                last_game_opponent = get_last_game(opponent)
                print(last_game_player, last_game_opponent)

                if last_game_player and last_game_opponent:
                    if last_game_player == last_game_opponent:
                        if player.rating < opponent.rating:
                            pairings.append((player, opponent, "white", "black"))
                        else:
                            pairings.append((opponent, player, "white", "black"))
                        print(
                            f"Paired {player.first_name} {player.last_name} with {opponent.first_name} {opponent.last_name}")
                    else:
                        if last_game_player == "white":
                            pairings.append((player, opponent, "black", "white"))
                        else:
                            pairings.append((player, opponent, "white", "black"))
                        print(
                            f"Paired {player.first_name} {player.last_name} with {opponent.first_name} {opponent.last_name} (color adjusted)")
            else:  # still needs to pair
                print(f"No valid opponents found for {player.first_name} {player.last_name}, adding to unpaired")
                unpaired.append(player)
        else:  # still needs to pair
            print(f"Player {player.first_name} {player.last_name} has no recent opponents, adding to unpaired")
            unpaired.append(player)
        print()

    return pairings, unpaired


def get_last_game(player):
    last_game = Game.objects.filter(
        (Q(white=player) & Q(black=player.opponent_one)) |
        (Q(white=player.opponent_one) & Q(black=player))
    ).order_by('-date_of_match').first()

    if last_game:
        if last_game.white == player:
            return "white"
        elif last_game.black == player:
            return "black"


def download_pairings(request):
    if request.method == 'POST':
        form = PairingDateForm(request.POST)
        if form.is_valid():
            date_of_match = form.cleaned_data['date']

            file_name = f'Pairings_{date_of_match}.xlsx'
            file_path = os.path.join(CREATED_PAIRING_FILES_DIR, file_name)

            # if file_name in os.listdir(CREATED_PAIRING_FILES_DIR):
            #     with open(file_path, 'rb') as f:
            #         response = HttpResponse(f.read(),
            #                                 content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            #         response['Content-Disposition'] = f'attachment; filename={file_name}'
            #         return response
            # else:
            file_path = write_pairings(date_of_match)

            with open(file_path, 'rb') as f:
                response = HttpResponse(f.read(),
                                        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = f'attachment; filename=Pairings_{date_of_match}.xlsx'
                return response
    else:
        form = PairingDateForm()

    return render(request, 'chess/pair.html', {'form': form})


def help_view(request):
    return render(request, 'chess/help.html', )


# -----------------------------------------------------------------------------------------------------------------------------------------------------------------


def search_results(request):
    form = SearchForm(request.GET or None)
    results = []

    if form.is_valid():
        query = form.cleaned_data['query']
        search_type = form.cleaned_data['search_board']

        # searching a board
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

        # searching a player
        elif search_type == 'Player':
            player_results = Player.objects.filter(
                Q(first_name__icontains=query) & Q(is_active=True) & Q(active_member=True) |
                Q(last_name__icontains=query) & Q(is_active=True) & Q(active_member=True)
            ).order_by('-rating', '-grade', 'last_name', 'first_name')
            results.extend(player_results)

        # search in a class
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
