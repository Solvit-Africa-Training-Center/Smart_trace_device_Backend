from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class User(AbstractUser):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('admin', 'Admin'),
        ('authority', 'Authority'),
    )

<<<<<<< HEAD
    email = models.EmailField(unique=True)
    phone = PhoneNumberField(blank=True, null=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    description = models.TextField(blank=True, null=True)
    lost_location = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

=======

    first_name = models.CharField(max_length=150, blank=True, null=True)
    last_name = models.CharField(max_length=150, blank=True, null=True)
    email = models.EmailField(unique=True)
    phone = PhoneNumberField(blank=True, null=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
>>>>>>> updated_functionality
    # Override username field to make it not unique
    username = models.CharField(max_length=150, unique=False)

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

    @classmethod
    def verify_code(cls, email, code):
<<<<<<< HEAD
        try:
            vc = cls.objects.get(email=email, code=code, is_used=False)
            vc.is_used = True
            vc.save()
            return True
        except cls.DoesNotExist:
=======
        from authentication.models import User
        try:
            user = User.objects.get(email=email)
            vc = cls.objects.get(user=user, code=code, is_used=False)
            vc.is_used = True
            vc.save()
            return True
        except (cls.DoesNotExist, User.DoesNotExist):
>>>>>>> updated_functionality
            return False

    @classmethod
    def resend_code(cls, email):
        from django.utils.crypto import get_random_string
<<<<<<< HEAD
        code = get_random_string(length=6, allowed_chars='0123456789')
        vc, created = cls.objects.update_or_create(email=email, defaults={'code': code, 'is_used': False})
=======
        from authentication.models import User
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return None
        code = get_random_string(length=6, allowed_chars='0123456789')
        vc, created = cls.objects.update_or_create(user=user, defaults={'code': code, 'is_used': False})
>>>>>>> updated_functionality
        return vc.code