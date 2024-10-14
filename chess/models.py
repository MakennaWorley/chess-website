from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.utils import timezone

'''class Club(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=15, unique=True)

    modified_by = models.ForeignKey(User, on_delete=models.RESTRICT)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    end_at = models.DateTimeField(default=None)

    def __str__(self):
        return self.name'''


class Player(models.Model):
    last_name = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    rating = models.IntegerField()
    beginning_rating = models.IntegerField(blank=True, null=True)
    grade = models.IntegerField(blank=True, null=True)
    lesson_class = models.ForeignKey('LessonClass', on_delete=models.RESTRICT, related_name='player_class', blank=True,
                                     null=True)
    active_member = models.BooleanField(default=True)
    is_volunteer = models.BooleanField(default=False)

    parent_or_guardian = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(max_length=200, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    additional_info = models.TextField(blank=True, null=True)

    opponent_one = models.ForeignKey('self', on_delete=models.RESTRICT, related_name='last_time_opponent', null=True,
                                     blank=True)
    opponent_two = models.ForeignKey('self', on_delete=models.RESTRICT, related_name='two_times_ago_opponent',
                                     null=True, blank=True)
    opponent_three = models.ForeignKey('self', on_delete=models.RESTRICT, related_name='three_times_ago_opponent',
                                       null=True, blank=True)
    # club = models.ForeignKey(Club, on_delete=models.RESTRICT)

    modified_by = models.ForeignKey(User, default="import", on_delete=models.RESTRICT)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    end_at = models.DateTimeField(default=None, blank=True, null=True)

    def __str__(self):
        if self.lesson_class:
            return self.name() + " | " + str(self.rating) + " | " + self.lesson_class.name
        else:
            return self.name() + " | " + str(self.rating)

    def name(self):
        return self.last_name + ", " + self.first_name

    def improved_rating(self):
        return self.rating - self.beginning_rating

    def search_view(self):
        lesson_class = self.lesson_class
        parent_or_guardian = self.parent_or_guardian
        email = self.email
        phone = self.phone

        if not lesson_class:
            lesson_class = "No class assigned"
        if not parent_or_guardian:
            parent_or_guardian = "No parent or guardian found"
        if not email:
            email = "No email found"
        if not phone:
            phone = "No phone found"

        return self.name() + " | " + str(self.rating) + " | " + str(
            self.grade) + " | " + lesson_class + " | " + parent_or_guardian + " | " + email + " | " + phone

    def update_rating(self, new_rating, opponent, modified_by):
        # Mark the current player instance as inactive and set the end date
        self.is_active = False
        self.end_at = timezone.now()
        self.save()

        # Preventing a player from having a rating less than 100
        if new_rating < 100:
            new_rating = 100

        # Create a new player instance with the updated rating and `is_active=True`
        # Updates player's last 3 opponents
        new_player = Player.objects.create(
            last_name=self.last_name,
            first_name=self.first_name,
            rating=new_rating,
            beginning_rating=self.beginning_rating,
            grade=self.grade,
            lesson_class=self.lesson_class,
            active_member=self.active_member,
            is_volunteer=self.is_volunteer,
            parent_or_guardian=self.parent_or_guardian,
            email=self.email,
            phone=self.phone,
            additional_info=self.additional_info,
            opponent_one=opponent,
            opponent_two=self.opponent_one,
            opponent_three=self.opponent_two,
            modified_by=modified_by,
            is_active=True,
        )

        return new_player


class LessonClass(models.Model):
    name = models.CharField(max_length=100)
    teacher = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='teacher')
    co_teacher = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='co_teacher', blank=True, null=True)
    # club = models.ForeignKey(Club, on_delete=models.RESTRICT)

    modified_by = models.ForeignKey(User, on_delete=models.RESTRICT)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    end_at = models.DateTimeField(default=None, blank=True, null=True)

    def __str__(self):
        return self.name


class RegisteredUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # club = models.ForeignKey(Club, on_delete=models.RESTRICT, blank=True, null=True)
    is_director = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    @staticmethod
    def authenticate_user(username, password):
        return authenticate(username=username, password=password)


class Game(models.Model):
    class Result(models.TextChoices):
        WHITE = 'White'
        BLACK = 'Black'
        DRAW = 'Draw'
        UNKNOWN = 'U'

    date_of_match = models.DateField()
    # club = models.ForeignKey(Club, on_delete=models.RESTRICT)
    white = models.ForeignKey(Player, on_delete=models.RESTRICT, related_name='game_as_white', blank=True, null=True)
    black = models.ForeignKey(Player, on_delete=models.RESTRICT, related_name='game_as_black', blank=True, null=True)
    board_letter = models.CharField(max_length=1)
    board_number = models.IntegerField()
    result = models.CharField(
        max_length=5,
        choices=Result.choices,
        default=Result.UNKNOWN,
        null=True
    )

    modified_by = models.ForeignKey(User, on_delete=models.RESTRICT)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    end_at = models.DateTimeField(default=None, blank=True, null=True)

    def __str__(self):
        white_player = f"{self.white.last_name}, {self.white.first_name}" if self.white else "No White Player"
        black_player = f"{self.black.last_name}, {self.black.first_name}" if self.black else "No Black Player"
        return f"{self.board_letter}{self.board_number} | {self.date_of_match} | White- {white_player} | Black- {black_player}"

    def get_board(self):
        return "" + self.board_letter + "-" + str(self.board_number) + ""

    def get_players(self):
        white_player = f"{self.white.last_name}, {self.white.first_name}" if self.white else "No White Player"
        black_player = f"{self.black.last_name}, {self.black.first_name}" if self.black else "No Black Player"
        return f"White- {white_player} | Black- {black_player}"

    @classmethod
    def add_game(cls, date_of_match, board_letter, board_number, white, black, result, modified_by):
        # Check if there's an active game on the same board
        if cls.objects.filter(date_of_match=date_of_match, board_letter=board_letter, board_number=board_number, is_active=True).exists():
            raise ValidationError(f"A game on board {board_letter}-{board_number} and {date_of_match} already exists.")

        # Create the new game
        new_game = cls.objects.create(
            date_of_match=date_of_match,
            board_letter=board_letter,
            board_number=board_number,
            white=white,
            black=black,
            result=result,
            modified_by=modified_by,
            is_active=True
        )
        return new_game

    def update_game(self, date_of_match, board_letter, board_number, white, black, result, modified_by):
        # Mark the current game instance as inactive and close it
        self.is_active = False
        self.end_at = timezone.now()
        self.save()

        # Create a new game instance with the updated values
        new_game = Game.add_game(
            date_of_match=date_of_match,
            board_letter=board_letter,
            board_number=board_number,
            white=white,
            black=black,
            result=result,
            modified_by=modified_by
        )

        return new_game
