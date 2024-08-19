from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth import authenticate


class Club(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Player(models.Model):
    name = models.CharField(max_length=100)
    current_rating = models.IntegerField()
    previous_rating = models.IntegerField()
    opponent_one = models.ForeignKey('self', on_delete=models.RESTRICT, related_name='last_time_opponent', null=False, blank=True)
    opponent_two = models.ForeignKey('self', on_delete=models.RESTRICT, related_name='two_times_ago_opponent', null=False, blank=True)
    opponent_three = models.ForeignKey('self', on_delete=models.RESTRICT, related_name='three_times_ago_opponent', null=False, blank=True)
    grade = models.IntegerField(default=0)
    club_name = models.ForeignKey(Club, on_delete=models.RESTRICT)
    parent_name = models.CharField(max_length=100)
    parent_email = models.EmailField(max_length=200)

    def __str__(self):
        return self.name


class LessonClass(models.Model):  # Renamed from Class to SchoolClass
    level = models.CharField(max_length=100)
    teacher = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='teacher')
    co_teacher = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='co_teacher', null=True)

    def __str__(self):
        return self.teacher.name


class RegisteredUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    club_name = models.ForeignKey(Club, on_delete=models.RESTRICT, blank=True, null=True)
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

    white = models.ForeignKey(Player, on_delete=models.RESTRICT, related_name='games_as_white')
    black = models.ForeignKey(Player, on_delete=models.RESTRICT, related_name='games_as_black')
    board_letter = models.CharField(max_length=1)
    board_number = models.IntegerField()
    result = models.CharField(
        max_length=1,
        choices=Result.choices,
        default=Result.DRAW,
    )

    def __str__(self):
        return f"{self.board_letter}{self.board_number}: White- {self.white.name}, Black- {self.black.name}"