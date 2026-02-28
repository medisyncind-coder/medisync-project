import random
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.mail import send_mail
from django.conf import settings

from accounts.models import User
from .models import Doctor, Lab


# ======================================================
# 📧 SEND OTP
# ======================================================
@api_view(['POST'])
def send_otp(request):
    email = request.data.get('email')

    if not email:
        return Response({'error': 'Email required'}, status=400)

    user, created = User.objects.get_or_create(
        email=email,
        defaults={'is_verified': False}
    )

    otp_code = str(random.randint(100000, 999999))
    user.otp = otp_code
    user.is_verified = False
    user.save()

    send_mail(
        subject="MediSync OTP Verification",
        message=f"Your OTP is {otp_code}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=True
    )

    return Response({'message': 'OTP sent successfully'})


# ======================================================
# 🔒 VERIFY OTP
# ======================================================
@api_view(['POST'])
def verify_otp(request):
    email = request.data.get('email')
    otp_input = request.data.get('otp')

    if not email or not otp_input:
        return Response({'error': 'Email and OTP required'}, status=400)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=404)

    if user.otp != otp_input:
        return Response({'error': 'Invalid OTP'}, status=400)

    # ✅ Verify user
    user.is_verified = True
    user.otp = None
    user.save()

    return Response({'message': 'OTP verified successfully'})
