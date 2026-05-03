from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from .manager import UserManager



class User(AbstractUser):

    username = None
    email = models.EmailField(unique=True)

    is_verified = models.BooleanField(default=False)
    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)

    def is_otp_valid(self):
        if not self.otp or not self.otp_created_at:
            return False
        return (timezone.now() - self.otp_created_at).seconds < 600  # 10 minutes

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        return self.email
