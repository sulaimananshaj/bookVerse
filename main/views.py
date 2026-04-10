from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from .forms import RegisterForm, LoginForm
from .models import CustomUser
from django.core.mail import send_mail
from django.conf import settings
from .models import Book
from .forms import BookUploadForm
from .models import Book, Bid, BID_INCREMENT


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
            user_obj = CustomUser.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
            if user:
                login(request, user)
                if user.is_staff:
                    return redirect('admin_dashboard')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid password.')
        except CustomUser.DoesNotExist:
            messages.error(request, 'No account found with this email.')
        except CustomUser.MultipleObjectsReturned:
            messages.error(request, 'Multiple accounts found with this email. Please contact admin.')
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
# ── BOOK DETAIL + BID FORM ──
def book_detail(request, book_id):
    if not request.user.is_authenticated:
        return redirect('home')

    book = Book.objects.get(id=book_id)

    # close auction if expired or max price reached
    if not book.is_sold:
        if book.is_expired() or book.current_price() >= book.max_price:
            book.close_auction()
            messages.info(request, 'This auction has ended.')

    bids = book.bids.all()
    return render(request, 'main/book_detail.html', {
        'book':          book,
        'bids':          bids,
        'bid_increment': BID_INCREMENT,
        'next_bid':      book.current_price() + BID_INCREMENT,
    })

# ── PLACE BID ──
def place_bid(request, book_id):
    if not request.user.is_authenticated:
        return redirect('home')

    book = Book.objects.get(id=book_id)

    # block uploader from bidding on own book
    if book.uploaded_by == request.user:
        messages.error(request, 'You cannot bid on your own book.')
        return redirect('book_detail', book_id=book_id)

    # block if auction closed
    if book.is_sold or book.is_expired():
        messages.error(request, 'This auction has already ended.')
        return redirect('book_detail', book_id=book_id)

    if request.method == 'POST':
        try:
            amount = round(float(request.POST.get('amount', 0)))
        except ValueError:
            messages.error(request, 'Invalid bid amount.')
            return redirect('book_detail', book_id=book_id)

        expected = round(float(book.current_price())) + BID_INCREMENT

        # validate increment
        if amount != expected:
            messages.error(request, f'Your bid must be exactly ₹{expected}.')
            return redirect('book_detail', book_id=book_id)

        # validate max price
        if amount > book.max_price:
            messages.error(request, f'Bid cannot exceed the max price ₹{book.max_price}.')
            return redirect('book_detail', book_id=book_id)

        Bid.objects.create(book=book, bidder=request.user, amount=amount)
        messages.success(request, f'Bid of ₹{amount} placed successfully!')

        # check if max price reached — close auction
        if amount >= book.max_price:
            book.close_auction()
            messages.info(request, 'Max price reached! Auction is now closed.')

    return redirect('book_detail', book_id=book_id)

# ── AJAX — live bid data for admin & book list ──
def live_bid_data(request, book_id):
    from django.http import JsonResponse
    book = Book.objects.get(id=book_id)
    return JsonResponse({
        'current_price': str(book.current_price()),
        'bid_count':     book.bids.count(),
        'is_sold':       book.is_sold,
        'is_expired':    book.is_expired(),
    })