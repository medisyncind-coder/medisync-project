from rest_framework.views import APIView
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import random

from .serializers import UserSerializer, VerifyAccountSerializers
from .emails import send_otp_via_email
from .models import User


def generate_otp():
    return str(random.randint(100000, 999999))


@method_decorator(csrf_exempt, name='dispatch')
class RegisterApi(APIView):

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({
                'status': 400,
                'message': 'Email and password are required'
            })

        user = User.objects.filter(email=email).first()

        # ✅ Already verified
        if user and user.is_verified:
            return Response({
                'status': 400,
                'message': 'User already verified'
            })

        # 🔁 Resend OTP
        if user and not user.is_verified:
            otp = generate_otp()
            user.otp = otp
            user.save()

            send_otp_via_email(user.email, otp)

            return Response({
                'status': 200,
                'message': 'OTP resent to email'
            })

        # 🆕 New user
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save(is_verified=False)

            otp = generate_otp()
            user.otp = otp
            user.save()

            send_otp_via_email(user.email, otp)

            return Response({
                'status': 200,
                'message': 'Registration successful. OTP sent to email'
            })

        return Response({
            'status': 400,
            'message': 'Validation error',
            'data': serializer.errors
        })


@method_decorator(csrf_exempt, name='dispatch')
class VerifyOtp(APIView):

    def post(self, request):
        serializer = VerifyAccountSerializers(data=request.data)

        if not serializer.is_valid():
            return Response({
                'status': 400,
                'message': 'Validation error',
                'data': serializer.errors
            })

        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']  # 🔥 string

        user = User.objects.filter(email=email).first()

        if not user:
            return Response({
                'status': 400,
                'message': 'Invalid email'
            })

        if user.otp != otp:
            return Response({
                'status': 400,
                'message': 'Wrong OTP'
            })

        user.is_verified = True
        user.otp = None
        user.save()

        return Response({
            'status': 200,
            'message': 'Account verified successfully'
        })
