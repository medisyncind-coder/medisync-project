from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from datetime import date
import random
import string
from accounts.models import User
from accounts.emails import send_otp_via_email
from .models import Doctor, Appointment, DoctorAvailability
from .forms import DoctorRegistrationForm, AppointmentForm


# ======================================================
# 🔢 OTP GENERATOR
# ======================================================
def generate_otp():
    return str(random.randint(100000, 999999))


# ======================================================
# 👨‍⚕️ DOCTOR LIST
# ======================================================
def doctor_page(request):
    doctors = Doctor.objects.filter(user__is_verified=True)
    return render(request, 'Doctor/doctor_page.html', {'doctors': doctors})


# ======================================================
# 👨‍⚕️ DOCTOR DETAIL
# ======================================================
def doctor_detail(request, id):
    doctor = get_object_or_404(Doctor, id=id, user__is_verified=True)

    photos = [
        doctor.photo_1, doctor.photo_2, doctor.photo_3,
        doctor.photo_4, doctor.photo_5, doctor.photo_6, doctor.photo_7
    ]

    return render(request, 'Doctor/doctor_detail.html', {
        'doctor': doctor,
        'photos': photos
    })


# ======================================================
# 👨‍⚕️ DOCTOR REGISTER (CSRF EXEMPT – PUBLIC SIGNUP)
# ======================================================
@csrf_exempt
def register_doctor(request):

    if request.method == "POST":
        form = DoctorRegistrationForm(request.POST, request.FILES)

        if form.is_valid():

            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            try:
                with transaction.atomic():

                    # 🔒 Prevent duplicate email
                    if User.objects.filter(email__iexact=email).exists():
                        messages.error(request, "Email already registered")
                        return render(request, 'Doctor/doctor_register.html', {'form': form})

                    # ✅ Create user (NO USERNAME)
                    user = User.objects.create_user(
                        email=email,
                        password=password
                    )

                    user.is_verified = False

                    # ✅ Generate OTP
                    otp = generate_otp()
                    user.otp = otp
                    user.save()

                    # ✅ Send OTP via REST or Email
                    send_otp_via_email(email, otp, role="Doctor")

                    # ✅ Create doctor profile
                    doctor = form.save(commit=False)
                    doctor.user = user
                    doctor.save()

                    request.session['otp_email'] = email

                    messages.success(request, "OTP sent successfully")
                    return redirect('verify_otp_page')

            except Exception as e:
                print("❌ REGISTER ERROR:", e)
                messages.error(request, "Registration failed")

        else:
            print("❌ FORM ERRORS:", form.errors)
            messages.error(request, "Invalid form data")

    else:
        form = DoctorRegistrationForm()

    return render(request, 'Doctor/doctor_register.html', {'form': form})


# ======================================================
# 🔒 VERIFY OTP (TEMPLATE FLOW)
# ======================================================
def verify_otp_page(request):

    if request.method == "POST":
        email = request.session.get('otp_email')
        otp = request.POST.get('otp')

        if not email:
            messages.error(request, "Session expired.")
            return redirect('doctor_register')

        try:
            user = User.objects.get(email=email)

            if user.otp == otp:
                user.is_verified = True
                user.otp = None
                user.save()

                messages.success(request, "Doctor verified successfully")
                return redirect('doctor_login')
            else:
                messages.error(request, "Invalid OTP")

        except User.DoesNotExist:
            messages.error(request, "User not found")

    return render(request, 'Doctor/verify_otp_page.html')


# ======================================================
# 🔑 LOGIN
# ======================================================
def doctor_login(request):
    return render(request, 'Doctor/doctor_login.html')


def do_doctor_login(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, email=email, password=password)

        if user is None:
            messages.error(request, "Invalid credentials")
            return redirect('doctor_login')

        if not user.is_verified:
            messages.error(request, "Please verify OTP first")
            return redirect('doctor_login')

        login(request, user)
        return redirect('doctor_dashboard')

    return redirect('doctor_login')


# ======================================================
# 🧑‍⚕️ DOCTOR DASHBOARD
# ======================================================
@login_required
def doctor_dashboard(request):
    doctor = Doctor.objects.filter(user=request.user).first()

    if not doctor:
        messages.error(request, "Doctor profile not found.")
        return redirect('doctor_login')

    today = date.today()

    appointments = Appointment.objects.filter(
        doctor_name=doctor.name,
        preferred_date=today
    )

    availability = DoctorAvailability.objects.filter(
        doctor=doctor,
        day=today.strftime("%A")
    ).first()

    return render(request, 'DoctorPortal/doctor_dashboard.html', {
        'doctor': doctor,
        'appointments': appointments,
        'availability': availability,
        'today': today
    })


# ======================================================
# ⏰ SET AVAILABILITY
# ======================================================
@login_required
def set_doctor_availability(request):
    doctor = get_object_or_404(Doctor, user=request.user)

    if request.method == "POST":
        DoctorAvailability.objects.update_or_create(
            doctor=doctor,
            day=request.POST.get('day'),
            defaults={
                'is_available': request.POST.get('is_available') == 'on',
                'start_time': request.POST.get('start_time'),
                'end_time': request.POST.get('end_time'),
                'reason': request.POST.get('reason')
            }
        )
        messages.success(request, "Availability updated")
        return redirect('doctor_dashboard')

    return render(request, 'DoctorPortal/availability.html')


# ======================================================
# 📅 BOOK APPOINTMENT
# ======================================================

def book_appointment(request, doctor_name, specialization):

    if request.method == "POST":
        form = AppointmentForm(request.POST)

        if form.is_valid():
            appointment = form.save(commit=False)

            # Doctor Info
            appointment.doctor_name = doctor_name
            appointment.specialization = specialization

            # Status & Booking ID
            appointment.status = "Pending"
            appointment.booking_id = generate_booking_id()

            # 🔒 Prevent Double Booking (Same Doctor Same Date Time)
            already_booked = Appointment.objects.filter(
                doctor_name=doctor_name,
                preferred_date=appointment.preferred_date,
                preferred_time=appointment.preferred_time,
                status__in=["Pending", "Approved"]
            ).exists()

            if already_booked:
                messages.error(request, "This time slot is already booked.")
                return render(request, 'Doctor/book_appointment.html', {
                    'form': form,
                    'doctor_name': doctor_name,
                    'specialization': specialization
                })

            appointment.save()

            messages.success(request, "Appointment booked successfully!")
            return redirect('home')

    else:
        form = AppointmentForm()

    return render(request, 'Doctor/book_appointment.html', {
        'form': form,
        'doctor_name': doctor_name,
        'specialization': specialization
    })

# ======================================================
# 🔢 BOOKING ID GENERATOR
# ======================================================
def generate_booking_id():
    return ''.join(
        random.choices(string.ascii_uppercase + string.digits, k=8)
    )


# ======================================================
# 🚪 LOGOUT
# ======================================================
def doctor_logout(request):
    logout(request)
    messages.success(request, "Logged out successfully")
    return redirect('home')
