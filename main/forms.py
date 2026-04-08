from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from .models import Book

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

class BookUploadForm(forms.ModelForm):
    class Meta:
        model  = Book
        fields = ['title', 'description', 'image', 'min_price', 'max_price', 'timer_duration']
        widgets = {
            'description':    forms.Textarea(attrs={'rows': 3}),
            'timer_duration': forms.Select(),
        }