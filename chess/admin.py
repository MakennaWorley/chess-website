from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import Player, LessonClass, RegisteredUser, Game
#from .models import Club, Player, LessonClass, RegisteredUser, Game

class RegisteredUserInline(admin.StackedInline):
    model = RegisteredUser
    can_delete = False

class UserAdmin(BaseUserAdmin):
    inlines = (RegisteredUserInline,)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
#admin.site.register(Club)
admin.site.register(Player)
admin.site.register(LessonClass)
#admin.site.register(RegisteredUser)
admin.site.register(Game)