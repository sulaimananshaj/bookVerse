from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from .forms import RegisterForm, LoginForm
from .models import CustomUser


#create views here

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'main/home.html')

def register_view(request):
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        user.email = form.cleaned_data['email']
        user.save()
        login(request, user)
        messages.success(request, 'Account created! Welcome to BookVerse.')
        return redirect('dashboard')
    return render(request, 'main/home.html', {
        'register_form': form,
        'tab': 'register'
    })

def login_view(request):
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email    = form.cleaned_data['email']
        password = form.cleaned_data['password']
        try:
            username = CustomUser.objects.get(email=email).username
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid password.')
        except CustomUser.DoesNotExist:
            messages.error(request, 'No account found with this email.')
    return render(request, 'main/home.html', {
        'login_form': form,
        'tab': 'login'
    })

def logout_view(request):
    logout(request)
    return redirect('home')

def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('home')
    return render(request, 'main/dashboard.html')