from django.db import models
from django.contrib.auth.models import AbstractUser
from .manager import UserManager


class User(AbstractUser):
    # ❌ username hata diya (email login ke liye)
    username = None

    # ✅ email primary identity
    email = models.EmailField(unique=True)

    # ✅ OTP + verification
    is_verified = models.BooleanField(default=False)
    otp = models.CharField(max_length=6, null=True, blank=True)

    # ✅ REQUIRED for custom user
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        return self.email
