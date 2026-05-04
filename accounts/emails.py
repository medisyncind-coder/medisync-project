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


def _send(subject, message, recipient):
    """Internal helper — silently skips if email is not configured."""
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[recipient],
            fail_silently=False,
        )
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")


# ──────────────────────────────────────────────
# DOCTOR APPOINTMENT NOTIFICATIONS
# ──────────────────────────────────────────────

def notify_appointment_approved(appointment):
    _send(
        subject="Your Appointment is Confirmed — MediSync",
        message=f"""Dear {appointment.full_name},

Great news! Your appointment with Dr. {appointment.doctor.name} has been approved.

  Booking ID : {appointment.booking_id}
  Date       : {appointment.appointment_date.strftime('%d %B %Y')}
  Time       : {appointment.appointment_time.strftime('%I:%M %p')}

Please arrive 10 minutes early. If you need to cancel, log in to MediSync and cancel before your appointment time.

Regards,
MediSync Team
""",
        recipient=appointment.email,
    )


def notify_appointment_rejected(appointment):
    _send(
        subject="Appointment Update — MediSync",
        message=f"""Dear {appointment.full_name},

We're sorry to inform you that your appointment with Dr. {appointment.doctor.name} on {appointment.appointment_date.strftime('%d %B %Y')} at {appointment.appointment_time.strftime('%I:%M %p')} could not be confirmed.

  Booking ID : {appointment.booking_id}

Please log in to MediSync to book a new appointment at a different time.

Regards,
MediSync Team
""",
        recipient=appointment.email,
    )


def notify_appointment_completed(appointment):
    _send(
        subject="Appointment Completed — MediSync",
        message=f"""Dear {appointment.full_name},

Your appointment with Dr. {appointment.doctor.name} on {appointment.appointment_date.strftime('%d %B %Y')} has been marked as completed.

  Booking ID : {appointment.booking_id}

Your prescription (if any) is available in your MediSync dashboard under Reports.

We hope you had a great experience. Thank you for choosing MediSync!

Regards,
MediSync Team
""",
        recipient=appointment.email,
    )


# ──────────────────────────────────────────────
# LAB APPOINTMENT NOTIFICATIONS
# ──────────────────────────────────────────────

def notify_lab_appointment_approved(appointment):
    _send(
        subject="Lab Test Booking Confirmed — MediSync",
        message=f"""Dear {appointment.full_name},

Your lab test booking at {appointment.lab.lab_name} has been confirmed.

  Booking ID : {appointment.booking_id}
  Test       : {appointment.test_name}
  Date       : {appointment.appointment_date.strftime('%d %B %Y')}
  Time       : {appointment.appointment_time.strftime('%I:%M %p')}

Please carry a valid ID when you visit. If you have any questions, contact the lab directly.

Regards,
MediSync Team
""",
        recipient=appointment.email,
    )


def notify_lab_appointment_rejected(appointment):
    _send(
        subject="Lab Test Booking Update — MediSync",
        message=f"""Dear {appointment.full_name},

Unfortunately, your lab test booking at {appointment.lab.lab_name} for {appointment.test_name} on {appointment.appointment_date.strftime('%d %B %Y')} has been cancelled.

  Booking ID : {appointment.booking_id}

Please log in to MediSync to rebook at a convenient time.

Regards,
MediSync Team
""",
        recipient=appointment.email,
    )


def notify_lab_test_completed(appointment):
    _send(
        subject="Lab Test Completed — MediSync",
        message=f"""Dear {appointment.full_name},

Your lab test ({appointment.test_name}) at {appointment.lab.lab_name} has been marked as completed.

  Booking ID : {appointment.booking_id}

Your report will be available in your MediSync dashboard shortly.

Regards,
MediSync Team
""",
        recipient=appointment.email,
    )


def notify_lab_report_ready(appointment):
    _send(
        subject="Your Lab Report is Ready — MediSync",
        message=f"""Dear {appointment.full_name},

Your lab report for {appointment.test_name} is now available in your MediSync dashboard.

  Booking ID : {appointment.booking_id}
  Lab        : {appointment.lab.lab_name}

Log in to MediSync and go to Reports to download your report.

Regards,
MediSync Team
""",
        recipient=appointment.email,
    )


def send_password_reset_email(email, reset_link):
    subject = "MediSync — Reset Your Password"
    message = f"""
Hello,

We received a request to reset your MediSync account password.

Click the link below to set a new password:
{reset_link}

This link will expire in 1 hour. If you did not request a password reset, please ignore this email.

Regards,
MediSync Team
"""
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[email],
        fail_silently=False
    )
