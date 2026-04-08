from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta

DEPARTMENT_CHOICES = [
    ('civil', 'Civil'),
    ('ec',    'EC'),
    ('eee',   'EEE'),
    ('cs',    'CS'),
]

class CustomUser(AbstractUser):
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