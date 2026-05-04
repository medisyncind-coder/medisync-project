from django.core.mail import send_mail
from django.core.cache import cache
from django.conf import settings
import random


def generate_otp():
    return str(random.randint(100000, 999999))


def send_otp_email(email, otp):
    send_mail(
        subject='MediSync Doctor OTP Verification',
        message=f'Your OTP is {otp}',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[email],
        fail_silently=False,
    )


def is_rate_limited(key, max_attempts, period_seconds):
    """
    Returns True if the caller has exceeded max_attempts within period_seconds.
    Uses Django's cache as the counter store.
    """
    count = cache.get(key, 0)
    if count >= max_attempts:
        return True
    cache.set(key, count + 1, period_seconds)
    return False

