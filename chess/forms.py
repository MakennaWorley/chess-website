from random import choices

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError

from .models import RegisteredUser, Game  # , Club


class LoginForm(AuthenticationForm):
    username = forms.CharField(max_length=254, widget=forms.TextInput(attrs={'autofocus': True}))
    password = forms.CharField(label=("Password"), widget=forms.PasswordInput)


class SignUpForm(forms.ModelForm):
    first_name = forms.CharField(label='First Name', max_length=100, required=True)
    last_name = forms.CharField(label='Last Name', max_length=100, required=True)
    username = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    #club_code = forms.CharField(max_length=100, required=False, label="Club Code (optional)")
    password1 = forms.CharField(widget=forms.PasswordInput(), label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput(), label="Confirm Password")

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name'] #, 'club_code']

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])

        # Save the user to create an instance in the database
        if commit:
            user.save()

        # Validate and assign the club code
        #club_code = self.cleaned_data.get("club_code")
        registered_user, created = RegisteredUser.objects.get_or_create(user=user)

        '''if club_code:
            try:
                registered_user.club = Club.objects.get(code=club_code)
                print(registered_user, registered_user.club, Club.objects.get(code=club_code))
                registered_user.club.save()
                return user
            except Club.DoesNotExist:
                registered_user.club = None

        print(registered_user, registered_user.club)'''
        registered_user.save()
        return user


SEARCH_CHOICES = [
    ('Player', 'Player'),
    ('Board', 'Board'),
    ('Class', 'Class')
]

class SearchForm(forms.Form):
    search_board = forms.ChoiceField(
        choices=SEARCH_CHOICES,
        widget=forms.RadioSelect(),
        initial='Player',
        required=True,
        label='Searching for:')
    query = forms.CharField(
        label='Keyword:',
        max_length=100,
        required=True,
    )