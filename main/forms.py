from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class RegisterForm(UserCreationForm):
    email=forms.EmailField(required=True)

    class Meta:
        model=CustomUser
        fields = [
            'username','email',
            'department','semester',
            'password1','password2'
        ]

class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)