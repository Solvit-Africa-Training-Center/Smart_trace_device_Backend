from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class User(AbstractUser):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('admin', 'Admin'),
        ('authority', 'Authority'),
    )

    serial_number = models.CharField(max_length=100, blank=True, null=True)
    device_image = models.ImageField(upload_to='user_devices/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    email = models.EmailField(unique=True)
    phone = PhoneNumberField(blank=True, null=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    lost_location = models.CharField(max_length=255, blank=True, null=True)

    # Override username field to make it not unique
    username = models.CharField(max_length=150, unique=False)

    # Set email as the unique identifier
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email


class VerificationCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.email} - {self.code}"