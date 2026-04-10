from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings

DEPARTMENT_CHOICES = [
    ('civil', 'Civil'),
    ('ec',    'EC'),
    ('eee',   'EEE'),
    ('cs',    'CS'),
]

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)  
    department = models.CharField(
        max_length=10,
        choices=DEPARTMENT_CHOICES,
        blank=True
    )
    semester = models.IntegerField(
        null=True,
        blank=True,
        choices=[(i, f'Sem {i}') for i in range(1, 9)]
    )

    def __str__(self):
        return self.email


TIMER_CHOICES = [
    (1,  '1 Day'),
    (3,  '3 Days'),
    (7,  '1 Week'),
]

STATUS_CHOICES = [
    ('pending',  'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
]

class Book(models.Model):
    title            = models.CharField(max_length=200)
    description      = models.TextField(blank=True)
    image            = models.ImageField(upload_to='books/')
    uploaded_by      = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='books')
    min_price        = models.DecimalField(max_digits=8, decimal_places=2)
    max_price        = models.DecimalField(max_digits=8, decimal_places=2)
    timer_duration   = models.IntegerField(choices=TIMER_CHOICES, default=3)
    bid_end_time     = models.DateTimeField(null=True, blank=True)
    status           = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    rejection_reason = models.TextField(blank=True)
    is_sold          = models.BooleanField(default=False)
    created_at       = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def approve(self):
        self.status = 'approved'
        self.bid_end_time = timezone.now() + timedelta(days=self.timer_duration)
        self.save()

    def current_price(self):
        top_bid = self.bids.first()
        if top_bid:
            return top_bid.amount
        return self.min_price

    def is_expired(self):
        if self.bid_end_time:
            return timezone.now() > self.bid_end_time
        return False

    def close_auction(self):
        top_bid = self.bids.first()
        if top_bid:
            self.is_sold = True
            self.save()
            # email the winner
            send_mail(
                subject=f'You won the bid for "{self.title}"!',
                message=f'Hi {top_bid.bidder.username},\n\n'
                        f'Congratulations! You won the bid for "{self.title}" '
                        f'at ₹{top_bid.amount}.\n\n'
                        f'Contact the seller {self.uploaded_by.username} to complete the purchase.\n'
                        f'Seller email: {self.uploaded_by.email}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[top_bid.bidder.email],
                fail_silently=True,
            )


BID_INCREMENT = 10  # ₹10 fixed increment

class Bid(models.Model):
    book      = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='bids')
    bidder    = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='bids')
    amount    = models.DecimalField(max_digits=8, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-amount']  # highest bid first

    def __str__(self):
        return f"{self.bidder.username} — ₹{self.amount} on {self.book.title}"