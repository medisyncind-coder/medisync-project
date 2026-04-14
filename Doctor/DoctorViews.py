from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from datetime import date
from django.utils import timezone
from datetime import datetime
import random
import string
from accounts.models import User
from accounts.emails import send_otp_via_email
from appointments.models import *
from .models import Doctor, DoctorAvailability, MedicalRecord
from .forms import DoctorRegistrationForm
from django.db.models import Q



from django.http import JsonResponse
from appointments.models import Appointment

def check_new_appointments(request):

    doctor = Doctor.objects.get(user=request.user)

    count = Appointment.objects.filter(
        doctor=doctor,
        status="Pending"
    ).count()

    return JsonResponse({"count": count})

# ======================================================
# 📡 LIVE DOCTOR STATUS API (Patient polling endpoint)
# ======================================================
def doctor_live_status(request, doctor_id):

    doctor = get_object_or_404(Doctor, id=doctor_id)

    # Get availability toggle
    availability = DoctorAvailability.objects.filter(doctor=doctor).first()
    is_available = availability.is_available if availability else True

    today = timezone.now().date()

    # All active (pending + approved) appointments today, in time order
    active_queue = Appointment.objects.filter(
        doctor=doctor,
        appointment_date=today,
        status__in=['Pending', 'Approved']
    ).order_by('appointment_time')

    total_queue = active_queue.count()
    queue_position = None
    estimated_wait = None

    # If a specific appointment_id is passed, calculate that patient's position
    appointment_id = request.GET.get('appointment_id')
    if appointment_id:
        try:
            patient_appt = Appointment.objects.get(
                id=int(appointment_id),
                doctor=doctor
            )
            ahead = active_queue.filter(
                appointment_time__lt=patient_appt.appointment_time
            ).count()
            queue_position = ahead + 1
            duration = doctor.appointment_duration or 15
            estimated_wait = ahead * duration  # minutes
        except (Appointment.DoesNotExist, ValueError):
            pass

    return JsonResponse({
        'is_available': is_available,
        'queue_position': queue_position,
        'estimated_wait': estimated_wait,
        'total_queue': total_queue,
    })

# ======================================================
# 🔢 OTP GENERATOR
# ======================================================
def generate_otp():
    return str(random.randint(100000, 999999))


# ======================================================
# 👨‍⚕️ DOCTOR LIST
# ======================================================
def doctor_page(request):

    search = request.GET.get('search')
    city = request.GET.get('city')

    doctors = Doctor.objects.filter(user__is_verified=True)

    if search:
        doctors = doctors.filter(
            Q(name__icontains=search) |
            Q(specialization__icontains=search)
        )

    # ❗ CHANGE HERE
    if city:
        doctors = doctors.filter(address__icontains=city)

    # ❗ CHANGE HERE
    cities = Doctor.objects.values_list('address', flat=True).distinct()

    context = {
        'doctors': doctors,
        'cities': cities
    }

    return render(request, 'Doctor/doctor_page.html', context)


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

            # ✅ OTP MATCH
            if user.otp == otp:
                user.is_verified = True
                user.otp = None
                user.save()

                # 🔥 LOGIN
                login(request, user)

                # 🧹 session clean
                request.session.pop('otp_email', None)

                messages.success(request, "Doctor verified & logged in successfully")

                # ✅ CORRECT REDIRECT
                return redirect('doctor_dashboard')   # 🔥 FIXED

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

    # Get logged-in doctor
    doctor = Doctor.objects.filter(user=request.user).first()

    if not doctor:
        messages.error(request, "Doctor profile not found.")
        return redirect("doctor_login")

    # Today's date
    today = timezone.now().date()

    # ==========================
    # Today's Appointments
    # ==========================
    today_appointments = Appointment.objects.filter(
        doctor=doctor,
        appointment_date=today
    )

    # Active appointments
    appointments = today_appointments.filter(
        status__in=["Pending", "Approved"]
    )

    # Completed today
    completed_today = today_appointments.filter(
        status="Completed"
    )

    # ==========================
    # Dashboard Statistics
    # ==========================

    # Pending Requests
    pending_count = Appointment.objects.filter(
        doctor=doctor,
        status="Pending"
    ).count()

    # Approved
    approved_count = Appointment.objects.filter(
        doctor=doctor,
        status="Approved"
    ).count()

    # Completed
    completed_count = Appointment.objects.filter(
        doctor=doctor,
        status="Completed"
    ).count()

    # Total patients (unique phone numbers)
    total_patients = Appointment.objects.filter(
        doctor=doctor
    ).values('contact_number').distinct().count()

    # Monthly earnings (example calculation)
    monthly_completed = Appointment.objects.filter(
        doctor=doctor,
        status="Completed",
        appointment_date__month=today.month
    ).count()

    consultation_fee = getattr(doctor, "consultation_fee", 500)

    monthly_earnings = monthly_completed * consultation_fee


    # ==========================
    # Context Data
    # ==========================

    context = {

        "doctor": doctor,

        "today": today,

        "appointments": appointments,

        "completed_today": completed_today,

        "pending_count": pending_count,

        "approved_count": approved_count,

        "completed_count": completed_count,

        "total_patients": total_patients,

        "monthly_earnings": monthly_earnings,

    }

    return render(request, "DoctorPortal/doctor_dashboard.html", context)
# ======================================================
# ⏰ SET AVAILABILITY
# ======================================================
@login_required
def set_doctor_availability(request):

    doctor = get_object_or_404(Doctor, user=request.user)

    if request.method == "POST":

        # checkbox value
        is_available = request.POST.get("is_available") == "on"

        # update or create availability
        DoctorAvailability.objects.update_or_create(
            doctor=doctor,
            defaults={
                "is_available": is_available
            }
        )

        if is_available:
            messages.success(request, "Doctor is now available for appointments.")
        else:
            messages.success(request, "Doctor marked as unavailable.")

        return redirect("doctor_dashboard")

    availability = DoctorAvailability.objects.filter(doctor=doctor).first()

    return render(request, "DoctorPortal/availability.html", {
        "availability": availability
    })

# # ======================================================
# # 📅 BOOK APPOINTMENT
# # ======================================================

@login_required
def doctor_appointments(request):

    doctor = Doctor.objects.filter(user=request.user).first()

    if not doctor:
        return render(request, "DoctorPortal/appointments.html", {
            "appointments": []
        })

    # ✅ All appointments (including cancelled)
    appointments = Appointment.objects.filter(
        doctor=doctor
    ).order_by('-created_at')

    # ✅ STATUS COUNTS
    pending_count = appointments.filter(status='Pending').count()
    approved_count = appointments.filter(status='Approved').count()
    completed_count = appointments.filter(status='Completed').count()
    cancelled_count = appointments.filter(status='Cancelled').count()  # 🔥 NEW

    context = {
        "appointments": appointments,
        "pending_count": pending_count,
        "approved_count": approved_count,
        "completed_count": completed_count,
        "cancelled_count": cancelled_count,  # 🔥 NEW
    }

    return render(request, "DoctorPortal/appointments.html", context)
@login_required
def patient(request, appointment_id):

    doctor = get_object_or_404(Doctor, user=request.user)

    today = timezone.now().date()

    # 🔒 ONLY TODAY APPOINTMENT ACCESS
    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        doctor=doctor,
        appointment_date=today
    )

    patient = appointment.patient

    # ================= SAVE PRESCRIPTION =================
    if request.method == "POST":

        medicine = request.POST.get("medicine")
        dosage = request.POST.get("dosage")
        instructions = request.POST.get("instructions")

        # ✅ SAVE MEDICINE ENTRY
        if medicine:
            Prescription.objects.create(
                appointment=appointment,
                medicine=medicine,
                dosage=dosage,
                instructions=instructions
            )

        # ✅ SAVE FILE (OPTIONAL)
        file = request.FILES.get("prescription_file")
        if file:
            appointment.prescription_file = file
            appointment.save()

        messages.success(request, "Prescription saved ✅")

        # 🔥 SAME PAGE RELOAD (NO ERROR)
        return redirect("doctor_patient", appointment_id=appointment.id)


    # ================= PATIENT HISTORY =================

    lab_reports = LabAppointment.objects.filter(
        patient=patient,
        report_file__isnull=False
    ).order_by("-appointment_date")

    records = MedicalRecord.objects.filter(
        patient=patient
    ).order_by("-uploaded_at")

    past_appointments = Appointment.objects.filter(
        patient=patient,
        prescription_file__isnull=False
    ).exclude(id=appointment.id).order_by("-appointment_date")

    prescriptions = appointment.prescriptions.all()

    # 🔥 IMPORTANT (LEFT PANEL KE LIYE)
    all_patients = Appointment.objects.filter(doctor=doctor, appointment_date=today)

    # ================= CONTEXT =================
    context = {
        "appointment": appointment,
        "patients": all_patients,   # 🔥 IMPORTANT
        "lab_reports": lab_reports,
        "records": records,
        "past_appointments": past_appointments,
        "prescriptions": prescriptions,
    }

    return render(request, "DoctorPortal/patients.html", context)

@login_required
def add_prescription(request, appointment_id):

    doctor = get_object_or_404(Doctor, user=request.user)

    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        doctor=doctor
    )

    if request.method == "POST":

        medicine = request.POST.get("medicine")
        dosage = request.POST.get("dosage")
        instructions = request.POST.get("instructions")

        # ✅ SAVE MEDICINE
        if medicine:
            Prescription.objects.create(
                appointment=appointment,
                medicine=medicine,
                dosage=dosage,
                instructions=instructions
            )

        # ✅ SAVE FILE
        file = request.FILES.get("prescription_file")
        if file:
            appointment.prescription_file = file
            appointment.save()

        messages.success(request, "Prescription saved ✅")

        # 🔥 FINAL FIX (IMPORTANT)
        return redirect("doctor_patient", appointment_id=appointment.id)

    return redirect("doctor_patient", appointment_id=appointment.id)

# # ======================================================
# # 🔢 BOOKING ID GENERATOR
# # ======================================================
# def generate_booking_id():
#     return ''.join(
#         random.choices(string.ascii_uppercase + string.digits, k=8)
#     )


# ======================================================
# 🚪 LOGOUT
# ======================================================
def doctor_logout(request):
    logout(request)
    messages.success(request, "Logged out successfully")
    return redirect('home')





@login_required
def approve_appointment(request, appointment_id):

    appointment = get_object_or_404(Appointment, id=appointment_id)

    appointment.status = "Approved"
    appointment.save()

    return redirect("doctor_appointments")


@login_required
def reject_appointment(request, appointment_id):

    appointment = get_object_or_404(Appointment, id=appointment_id)

    appointment.status = "Rejected"
    appointment.save()

    return redirect("doctor_appointments")



@login_required
def complete_appointment(request, appointment_id):

    appointment = get_object_or_404(Appointment, id=appointment_id)

    appointment.status = "Completed"
    appointment.save()

    return redirect("doctor_appointments")


@login_required
def doctor_patients(request):

    doctor = Doctor.objects.get(user=request.user)

    patients = Appointment.objects.filter(
        doctor=doctor
    ).order_by('-appointment_date')

    return render(request,"DoctorPortal/patients.html",{
        "patients":patients
    })
    

@login_required
def doctor_payments(request):

    payments = []   # you can connect payment model later

    context = {
        "payments": payments
    }

    return render(request, "DoctorPortal/payments.html", context)


@login_required
def doctor_notifications(request):

    notifications = []   # later you can connect notification model

    context = {
        "notifications": notifications
    }

    return render(request, "DoctorPortal/notifications.html", context)


@login_required
def doctor_settings(request):

    context = {}

    return render(request, "DoctorPortal/settings.html", context)


@login_required
def doctor_profile_edit(request):

    doctor = Doctor.objects.get(user=request.user)

    if request.method == "POST":

        # ❌ Ye fields change nahi honge
        # doctor.name
        # doctor.qualification
        # doctor.clinic_name
        # doctor.profile_photo

        # ✅ Editable Fields
        doctor.specialization = request.POST.get("specialization")
        doctor.experience = request.POST.get("experience")
        doctor.contact_number = request.POST.get("contact_number")

        doctor.address = request.POST.get("address") or doctor.address

        doctor.consultation_fee = request.POST.get("consultation_fee")

        doctor.available_days = request.POST.getlist("available_days")

        doctor.start_time = request.POST.get("start_time") or doctor.start_time
        doctor.end_time = request.POST.get("end_time") or doctor.end_time

        doctor.appointment_duration = request.POST.get("appointment_duration")

        doctor.full_address = request.POST.get("full_address")
        doctor.pincode = request.POST.get("pincode")
        doctor.emergency_number = request.POST.get("emergency_number")

        doctor.bio = request.POST.get("bio")
        doctor.location_link = request.POST.get("location_link")

        doctor.save()

        return redirect("doctor_detail", id=doctor.id)

    return render(request, "DoctorPortal/doctor_profile_edit.html", {"doctor": doctor})

@login_required
def doctor_lab_reports(request):
    return render(request, "DoctorPortal/doctor_lab_reports.html")