from django.contrib.auth.models import AbstractUser
from django.db import models


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