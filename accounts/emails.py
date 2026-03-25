from django.core.mail import send_mail
from django.conf import settings


# def send_otp_via_email(email, otp):
#     print("====== OTP FUNCTION CALLED ======")
#     print("EMAIL RECEIVED:", email)
#     print("OTP SENT:", otp)

#     subject = "MediSync Doctor Account Verification"

#     message = f"""
# Dear Doctor,

# Your OTP for account verification is: {otp}

# Please do not share this OTP with anyone.

# Regards,
# MediSync Team
# """

#     send_mail(
#         subject=subject,
#         message=message,
#         from_email=settings.EMAIL_HOST_USER,
#         recipient_list=[email],
#         fail_silently=False
#     )

#     print("====== MAIL SENT SUCCESS ======")

def send_otp_via_email(email, otp, role="Doctor"):

    print("====== OTP FUNCTION CALLED ======")
    print("EMAIL RECEIVED:", email)
    print("OTP SENT:", otp)

    if role == "Doctor":
        subject = "MediSync Doctor Account Verification"
        message = f"""
Dear Doctor,

Your OTP for Doctor Account Verification is: {otp}

This OTP will expire in 5 minutes.

Please do not share this OTP with anyone.

Regards,
MediSync Team
"""

    elif role == "Lab":
        subject = "MediSync Lab Account Verification"
        message = f"""
Dear Lab Administrator,

Welcome to MediSync!

Your OTP for Lab Registration Verification is: {otp}

This OTP will expire in 5 minutes.

After verification, you will be able to add your diagnostic tests and manage bookings.

Please do not share this OTP with anyone.

Regards,
MediSync Team
"""

    elif role == "Patient":
        subject = "MediSync Patient Account Verification"
        message = f"""
Dear Patient,

Welcome to MediSync!

Your OTP for Patient Account Verification is: {otp}

This OTP will expire in 5 minutes.

After verification, you will be able to book doctor appointments, lab tests, and manage your health records.

Please do not share this OTP with anyone.

Regards,
MediSync Team
"""


    else:
        subject = "MediSync Account Verification"
        message = f"""
Your OTP is: {otp}
"""

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[email],
        fail_silently=False
    )

    print("====== MAIL SENT SUCCESS ======")
    
    
    
    