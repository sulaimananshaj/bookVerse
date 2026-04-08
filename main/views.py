from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from .forms import RegisterForm, LoginForm
from .models import CustomUser
from django.core.mail import send_mail
from django.conf import settings
from .models import Book
from .forms import BookUploadForm


#create views here

def home(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
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
                # ── redirect admin to admin dashboard ──
                if user.is_staff:
                    return redirect('admin_dashboard')
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

# ── BOOK UPLOAD ──
def upload_book(request):
    if not request.user.is_authenticated:
        return redirect('home')
    form = BookUploadForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        book = form.save(commit=False)
        book.uploaded_by = request.user
        book.save()
        messages.success(request, 'Book submitted! Waiting for admin approval.')
        return redirect('dashboard')
    return render(request, 'main/upload_book.html', {'form': form})

# ── BOOK LIST (approved only) ──
def book_list(request):
    if not request.user.is_authenticated:
        return redirect('home')
    books = Book.objects.filter(status='approved', is_sold=False)
    return render(request, 'main/book_list.html', {'books': books})

# ── ADMIN LOGIN ──
def admin_login(request):
    if request.method == 'POST':
        email    = request.POST.get('email')
        password = request.POST.get('password')
        try:
            username = CustomUser.objects.get(email=email, is_staff=True).username
            user = authenticate(request, username=username, password=password)
            if user and user.is_staff:
                login(request, user)
                return redirect('admin_dashboard')
            else:
                messages.error(request, 'Invalid credentials or not an admin.')
        except CustomUser.DoesNotExist:
            messages.error(request, 'No admin account found.')
    return render(request, 'main/admin_login.html')

# ── ADMIN DASHBOARD ──
def admin_dashboard(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('admin_login')
    pending_books  = Book.objects.filter(status='pending').order_by('-created_at')
    approved_books = Book.objects.filter(status='approved').order_by('-created_at')
    return render(request, 'main/admin_dashboard.html', {
        'pending_books':  pending_books,
        'approved_books': approved_books,
    })

# ── APPROVE BOOK ──
def approve_book(request, book_id):
    if not request.user.is_staff:
        return redirect('admin_login')
    book = Book.objects.get(id=book_id)
    book.approve()
    # Email all registered users
    all_users = CustomUser.objects.exclude(is_staff=True)
    emails = [u.email for u in all_users if u.email]
    send_mail(
        subject=f'New Book Available for Bidding — {book.title}',
        message=f'Hi!\n\nA new book "{book.title}" is now available for bidding on BookVerse.\n'
                f'Price range: ₹{book.min_price} – ₹{book.max_price}\n'
                f'Bidding closes in {book.timer_duration} day(s).\n\n'
                f'Login to BookVerse to place your bid!',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=emails,
        fail_silently=True,
    )
    messages.success(request, f'"{book.title}" approved and users notified.')
    return redirect('admin_dashboard')

# ── REJECT BOOK ──
def reject_book(request, book_id):
    if not request.user.is_staff:
        return redirect('admin_login')
    if request.method == 'POST':
        book = Book.objects.get(id=book_id)
        reason = request.POST.get('reason', 'No reason provided.')
        book.status = 'rejected'
        book.rejection_reason = reason
        book.save()
        # Email the uploader
        send_mail(
            subject=f'Your book "{book.title}" was not approved',
            message=f'Hi {book.uploaded_by.username},\n\n'
                    f'Unfortunately your book "{book.title}" was rejected.\n\n'
                    f'Reason: {reason}\n\n'
                    f'You can re-upload with corrections.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[book.uploaded_by.email],
            fail_silently=True,
        )
        messages.success(request, f'"{book.title}" rejected and uploader notified.')
    return redirect('admin_dashboard')