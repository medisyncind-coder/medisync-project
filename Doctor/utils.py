from django.core.mail import send_mail
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

