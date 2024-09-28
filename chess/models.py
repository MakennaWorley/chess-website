from datetime import timezone

from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth import authenticate


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
    lesson_class = models.ForeignKey('LessonClass', on_delete=models.RESTRICT, related_name='player_class', blank=True, null=True)
    active_member = models.BooleanField(default=True)
    is_volunteer = models.BooleanField(default=False)

    parent_or_guardian = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(max_length=200, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    additional_info = models.TextField(blank=True, null=True)

    opponent_one = models.ForeignKey('self', on_delete=models.RESTRICT, related_name='last_time_opponent', null=True, blank=True)
    opponent_two = models.ForeignKey('self', on_delete=models.RESTRICT, related_name='two_times_ago_opponent', null=True, blank=True)
    opponent_three = models.ForeignKey('self', on_delete=models.RESTRICT, related_name='three_times_ago_opponent', null=True, blank=True)
    #club = models.ForeignKey(Club, on_delete=models.RESTRICT)

    modified_by = models.ForeignKey(User, default="import", on_delete=models.RESTRICT)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    end_at = models.DateTimeField(default=None, blank=True, null=True)

    def __str__(self):
        if self.lesson_class:
            return self.name() + " | "+ str(self.rating) + " | " + self.lesson_class.name
        else:
            return self.name() + " | "+ str(self.rating) + " | No class assigned"

    def name(self):
        return self.last_name + ", " + self.first_name


class LessonClass(models.Model):
    name = models.CharField(max_length=100)
    teacher = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='teacher')
    co_teacher = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='co_teacher', blank=True, null=True)
    #club = models.ForeignKey(Club, on_delete=models.RESTRICT)

    modified_by = models.ForeignKey(User, on_delete=models.RESTRICT)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    end_at = models.DateTimeField(default=None, blank=True, null=True)

    def __str__(self):
        return self.name


class RegisteredUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    #club = models.ForeignKey(Club, on_delete=models.RESTRICT, blank=True, null=True)
    is_director = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    @staticmethod
    def authenticate_user(username, password):
        return authenticate(username=username, password=password)


class Game(models.Model):
    class Result(models.TextChoices):
        WHITE_WIN = 'W', 'White'
        BLACK_WIN = 'B', 'Black'
        DRAW = 'D', 'Draw'
        UNKNOWN = 'U', 'Unknown'

    date_of_match = models.DateField()
    #club = models.ForeignKey(Club, on_delete=models.RESTRICT)
    white = models.ForeignKey(Player, on_delete=models.RESTRICT, related_name='game_as_white', blank=True, null=True)
    black = models.ForeignKey(Player, on_delete=models.RESTRICT, related_name='game_as_black', blank=True, null=True)
    board_letter = models.CharField(max_length=1)
    board_number = models.IntegerField()
    result = models.CharField(
        max_length=1,
        choices=Result.choices,
        default=Result.UNKNOWN,
    )

    modified_by = models.ForeignKey(User, on_delete=models.RESTRICT)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    end_at = models.DateTimeField(default=None, blank=True, null=True)

    def __str__(self):
        white_player = f"{self.white.last_name}, {self.white.first_name}" if self.white else "No White Player"
        black_player = f"{self.black.last_name}, {self.black.first_name}" if self.black else "No Black Player"
        return f"{self.board_letter}{self.board_number} | White- {white_player} | Black- {black_player}"

    def get_board(self):
        return "" + self.board_letter + str(self.board_number) + ""