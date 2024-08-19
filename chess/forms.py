from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError

from .models import RegisteredUser


class LoginForm(AuthenticationForm):
    username = forms.CharField(max_length=254, widget=forms.TextInput(attrs={'autofocus': True}))
    password = forms.CharField(label=("Password"), widget=forms.PasswordInput)


class SignUpForm(forms.ModelForm):
    username = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    club_code = forms.CharField(max_length=100, required=False, label="Club Code (optional)")
    password1 = forms.CharField(widget=forms.PasswordInput(), label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput(), label="Confirm Password")

    class Meta:
        model = User
        fields = ['username', 'email']

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
        if commit:
            try:
                user.save()
                club_code = self.cleaned_data.get("club_code")
                if club_code:
                    try:
                        club = Club.objects.get(name=club_code)
                    except ObjectDoesNotExist:
                        club = None
                else:
                    club = None

                # Check if a RegisteredUser already exists
                try:
                    registered_user, created = RegisteredUser.objects.get_or_create(user=user,
                                                                                    defaults={'club_name': club})
                    if not created:
                        registered_user.club_name = club
                        registered_user.save()
                except IntegrityError:
                    pass  # Handle this scenario or log an error if needed

            except IntegrityError as e:
                # Log the error or handle it as appropriate
                print(f"IntegrityError occurred: {e}")
                return None
        return user