from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str

import random


from accounts.emails import send_otp_via_email, send_password_reset_email
from .utils import is_rate_limited
from .forms import PatientRegistrationForm
from .models import Doctor, Lab, MedicalRecord, Patient
from appointments.models import Appointment, LabAppointment

User = get_user_model()
_token_generator = PasswordResetTokenGenerator()


# ================= OTP GENERATOR ================= #
def generate_otp():
    return str(random.randint(100000, 999999))


# ================= USER HOME ================= #
def user_home(request):
    return render(request, 'User/user_home.html')


# ================= LOGIN PAGE ================= #
def patient_login(request):
    return render(request, 'Patient/patient_login.html')


# ================= REGISTER ================= #
def register_patient(request):

    if request.method == "POST":
        form = PatientRegistrationForm(request.POST, request.FILES)

        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            full_name = form.cleaned_data['name']

            if is_rate_limited(f"otp_send:{email}", max_attempts=3, period_seconds=3600):
                messages.error(request, "Too many attempts. Please try again in 1 hour.")
                return render(request, 'Patient/patient_register.html', {'form': form})

            try:
                # ✅ Handle existing unverified user (stale/incomplete registration)
                existing_user = User.objects.filter(email__iexact=email).first()
                if existing_user:
                    if existing_user.is_verified:
                        messages.error(request, "Email already registered. Please login.")
                        return render(request, 'Patient/patient_register.html', {'form': form})
                    else:
                        # Delete stale unverified user and their patient record
                        existing_user.delete()

                with transaction.atomic():
                    # ✅ Split name
                    name_parts = full_name.strip().split()
                    first_name = name_parts[0]
                    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

                    # ✅ Create user
                    user = User.objects.create_user(
                        email=email,
                        password=password
                    )
                    user.first_name = first_name
                    user.last_name = last_name
                    user.is_verified = False
                    otp = generate_otp()
                    user.otp = otp
                    user.otp_created_at = timezone.now()
                    user.save()

                    # ✅ Signal already created a blank Patient — just update it
                    patient = Patient.objects.get(user=user)
                    patient.name                = form.cleaned_data.get("name") or ""
                    patient.phone               = form.cleaned_data.get("phone") or ""
                    patient.address             = form.cleaned_data.get("address") or ""
                    patient.date_of_birth       = form.cleaned_data.get("date_of_birth")
                    patient.gender              = form.cleaned_data.get("gender") or ""
                    patient.blood_group         = form.cleaned_data.get("blood_group") or ""
                    patient.full_address        = form.cleaned_data.get("full_address") or ""
                    patient.pincode             = form.cleaned_data.get("pincode") or ""
                    patient.emergency_contact   = form.cleaned_data.get("emergency_contact") or ""
                    patient.allergies           = form.cleaned_data.get("allergies") or ""
                    patient.medical_conditions  = form.cleaned_data.get("medical_conditions") or ""
                    if form.cleaned_data.get("profile_photo"):
                        patient.profile_photo   = form.cleaned_data.get("profile_photo")
                    patient.save()

                # ✅ Send OTP outside transaction so email failure doesn't rollback DB
                try:
                    send_otp_via_email(email, otp, role="Patient")
                except Exception as email_error:
                    print("❌ EMAIL ERROR:", email_error)

                request.session['otp_email'] = email
                messages.success(request, "OTP sent to your email.")
                return redirect('patient_verify_otp')

            except Exception as e:
                import traceback
                traceback.print_exc()
                messages.error(request, f"Registration failed: {str(e)}")

        else:
            print("❌ FORM ERRORS:", form.errors)
            messages.error(request, "Invalid form data")

    else:
        form = PatientRegistrationForm()

    return render(request, 'Patient/patient_register.html', {'form': form})
# ================= VERIFY OTP ================= #
def patient_verify_otp(request):

    if request.method == "POST":
        email = request.session.get('otp_email')
        otp = request.POST.get('otp')

        if not email:
            messages.error(request, "Session expired.")
            return redirect('patient_register')

        if is_rate_limited(f"otp_verify:{email}", max_attempts=5, period_seconds=600):
            messages.error(request, "Too many incorrect attempts. Please wait 10 minutes.")
            return render(request, 'Patient/verify_otp.html')

        try:
            user = User.objects.get(email=email)

            # ✅ OTP MATCH
            if not user.is_otp_valid():
                messages.error(request, "OTP has expired. Please register again.")
                return redirect('patient_register')

            if user.otp == otp:
                user.is_verified = True
                user.otp = None
                user.otp_created_at = None
                user.save()

                # 🔥 LOGIN KARO
                login(request, user)

                # 🧹 session clean
                request.session.pop('otp_email', None)

                messages.success(request, "Account verified & logged in successfully")

                # 🚀 DIRECT DASHBOARD
                return redirect('patient_dashboard')

            else:
                messages.error(request, "Invalid OTP")

        except User.DoesNotExist:
            messages.error(request, "User not found")

    return render(request, 'Patient/verify_otp.html')


# ================= LOGIN ================= #
def do_patient_login(request):

    if request.method == "POST":

        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, email=email, password=password)

        if user is None:
            messages.error(request, "Invalid email or password")
            return redirect('patient_login')   # ✅ FIXED

        if not user.is_verified:
            messages.error(request, "Please verify OTP first")
            return redirect('patient_login')   # ✅ FIXED

        if not user.is_active:
            messages.error(request, "Account is disabled")
            return redirect('patient_login')   # ✅ FIXED

        login(request, user)
        return redirect('patient_dashboard')   # ✅ FIXED

    return redirect('patient_login')           # ✅ FIXED

# ================= LOGOUT ================= #
@login_required
def user_logout(request):
    logout(request)  # 🔐 session clear
    messages.success(request, "You have been logged out successfully")
    return redirect('home')  # 🏠 home page

# ================= DASHBOARD ================= #

@login_required
def user_dashboard(request):

    patient = request.user
    today = timezone.localdate()   # ✅ safest

    # ================= DOCTOR APPOINTMENTS =================
    appointments = Appointment.objects.filter(patient=patient)

    # ================= STATS =================
    total_appointments = appointments.exclude(status="Cancelled").count()

    completed = appointments.filter(status="Completed").count()
    pending = appointments.filter(status="Pending").count()

    # ================= TODAY (DOCTOR) =================
    today_appointments = appointments.filter(
        appointment_date=today   # ✅ DateField fix
    ).exclude(status="Cancelled").order_by("appointment_time")

    # ================= TODAY (LAB) =================
    today_lab_bookings = LabAppointment.objects.filter(
        patient=patient,
        appointment_date=today   # ✅ DateField fix
    ).exclude(status="Cancelled").order_by("appointment_time")

    # ================= PAST (DOCTOR) =================
    past_appointments = appointments.filter(
        appointment_date__lt=today   # ✅ DateField fix
    ).exclude(status="Cancelled").order_by("-appointment_date", "-appointment_time")

    # ================= PAST COUNT =================
    past_count = past_appointments.count()

    # ================= CONTEXT =================
    context = {
        "total_appointments": total_appointments,
        "completed": completed,
        "pending": pending,
        "past_count": past_count,

        "today_appointments": today_appointments,
        "today_lab_bookings": today_lab_bookings,
        "past_appointments": past_appointments,
    }

    return render(request, "Patient/patient_dashboard.html", context)

# ================= SEARCH DOCTORS ================= #
@login_required
def search_doctors(request):

    query = request.GET.get("q", "")
    doctors = Doctor.objects.all()

    if query:
        doctors = doctors.filter(
            Q(name__icontains=query) |
            Q(specialization__icontains=query) |
            Q(clinic_name__icontains=query)
        )

    return render(request, "UserPortal/search_doctors.html", {"doctors": doctors})


# ================= BOOK APPOINTMENT ================= #
@login_required
def my_bookings(request):

    patient = request.user
    today = timezone.localdate()

    # ================= DOCTOR =================
    doctor_bookings = Appointment.objects.filter(
        patient=patient,
        appointment_date__gte=today
    ).exclude(status="Cancelled")

    # ================= LAB =================
    lab_bookings = LabAppointment.objects.filter(
        patient=patient,
        appointment_date__gte=today
    ).exclude(status="Cancelled")

    # ================= COMBINE =================
    bookings = []

    for a in doctor_bookings:
        bookings.append({
            "type": "Doctor",
            "name": a.doctor.name,
            "date": a.appointment_date,
            "time": a.appointment_time,
            "status": a.status,
            "id": a.id,
            "doctor_id": a.doctor.id,        # ← only new line
        })


    for l in lab_bookings:
        bookings.append({
            "type": "Lab",
            "name": l.test_name,
            "date": l.appointment_date,
            "time": l.appointment_time,
            "status": l.status,
            "id": l.id
        })

    # 🔥 SORT (nearest first)
    bookings = sorted(bookings, key=lambda x: (x["date"], x["time"]))

    return render(request, "Patient/my_bookings.html", {
        "bookings": bookings
    })

# ================= RESCHEDULE ================= #
@login_required
def reschedule_appointment(request, type, id):
    from datetime import datetime, timedelta
    from appointments.views import generate_slots, generate_lab_slots
    from Doctor.models import DoctorAvailability, LabAvailability

    today = datetime.today().date()

    # ── Fetch the booking ──
    if type == "doctor":
        booking = get_object_or_404(Appointment, id=id, patient=request.user)
        doctor = booking.doctor

        if booking.status not in ("Pending", "Approved"):
            messages.error(request, "Only pending or approved appointments can be rescheduled.")
            return redirect("my_bookings")

        # Build available dates (next 30 days, matching doctor's weekdays)
        doctor_days = [d.strip() for d in (doctor.available_days or [])]
        available_dates = [
            today + timedelta(days=i)
            for i in range(30)
            if (today + timedelta(days=i)).strftime("%a") in doctor_days
        ]

        # Selected date from GET param
        date_str = request.GET.get("date")
        selected_date = today
        if date_str:
            try:
                selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                pass
        if selected_date.strftime("%a") not in doctor_days:
            selected_date = available_dates[0] if available_dates else today

        # Check toggle
        avail = DoctorAvailability.objects.filter(doctor=doctor).first()
        if avail and not avail.is_available:
            messages.error(request, "Doctor is currently not accepting appointments.")
            return redirect("my_bookings")

        duration = doctor.appointment_duration or 15
        slots = generate_slots(doctor.start_time, doctor.end_time, duration, for_date=selected_date)
        booked = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=selected_date,
            status__in=["Pending", "Approved"]
        ).exclude(id=booking.id).values_list("appointment_time", flat=True)
        available_slots = [s for s in slots if s not in booked]

        if request.method == "POST":
            new_date_str = request.POST.get("appointment_date")
            new_time_str = request.POST.get("appointment_time")
            try:
                new_date = datetime.strptime(new_date_str, "%Y-%m-%d").date()
                new_time = datetime.strptime(new_time_str, "%H:%M:%S").time()
            except (ValueError, TypeError):
                messages.error(request, "Invalid date or time selected.")
                return redirect("reschedule_appointment", type=type, id=id)

            if new_date < today:
                messages.error(request, "Cannot reschedule to a past date.")
                return redirect("reschedule_appointment", type=type, id=id)

            booking.appointment_date = new_date
            booking.appointment_time = new_time
            booking.status = "Pending"
            booking.save()
            messages.success(request, "Appointment rescheduled successfully.")
            return redirect("my_bookings")

        return render(request, "Patient/reschedule.html", {
            "booking": booking,
            "booking_type": "doctor",
            "available_dates": available_dates,
            "selected_date": selected_date,
            "slots": available_slots,
        })

    elif type == "lab":
        booking = get_object_or_404(LabAppointment, id=id, patient=request.user)
        lab = booking.lab

        if booking.status not in ("Pending", "Approved"):
            messages.error(request, "Only pending or approved bookings can be rescheduled.")
            return redirect("my_bookings")

        lab_days_raw = [d.strip() for d in (lab.operating_days or "").split(",") if d.strip()]
        available_dates = [
            today + timedelta(days=i)
            for i in range(30)
            if (today + timedelta(days=i)).strftime("%A") in lab_days_raw
        ]

        date_str = request.GET.get("date")
        selected_date = today
        if date_str:
            try:
                selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                pass
        if selected_date.strftime("%A") not in lab_days_raw:
            selected_date = available_dates[0] if available_dates else today

        avail, _ = LabAvailability.objects.get_or_create(lab=lab)
        if not avail.is_available:
            messages.error(request, "Lab is currently not accepting bookings.")
            return redirect("my_bookings")

        slots = generate_lab_slots(lab.opening_time, lab.closing_time, 15)
        booked = LabAppointment.objects.filter(
            lab=lab,
            appointment_date=selected_date,
            status__in=["Pending", "Approved"]
        ).exclude(id=booking.id).values_list("appointment_time", flat=True)
        available_slots = [s for s in slots if s not in booked]

        if request.method == "POST":
            new_date_str = request.POST.get("appointment_date")
            new_time_str = request.POST.get("appointment_time")
            try:
                new_date = datetime.strptime(new_date_str, "%Y-%m-%d").date()
                new_time = datetime.strptime(new_time_str, "%H:%M:%S").time()
            except (ValueError, TypeError):
                messages.error(request, "Invalid date or time selected.")
                return redirect("reschedule_appointment", type=type, id=id)

            if new_date < today:
                messages.error(request, "Cannot reschedule to a past date.")
                return redirect("reschedule_appointment", type=type, id=id)

            booking.appointment_date = new_date
            booking.appointment_time = new_time
            booking.status = "Pending"
            booking.save()
            messages.success(request, "Lab test rescheduled successfully.")
            return redirect("my_bookings")

        return render(request, "Patient/reschedule.html", {
            "booking": booking,
            "booking_type": "lab",
            "available_dates": available_dates,
            "selected_date": selected_date,
            "slots": available_slots,
        })

    messages.error(request, "Invalid booking type.")
    return redirect("my_bookings")


# ================= CANCEL ================= #
@login_required
def cancel_appointment(request, type, id):

    # ================= GET OBJECT =================
    if type == "doctor":
        booking = get_object_or_404(
            Appointment,
            id=id,
            patient=request.user   # ✅ FIXED
        )

    elif type == "lab":
        booking = get_object_or_404(
            LabAppointment,
            id=id,
            patient=request.user   # ✅ FIXED
        )

    else:
        messages.error(request, "Invalid booking type")
        return redirect("my_bookings")

    # ================= VALIDATION =================
    if booking.status == "Completed":
        messages.error(request, "Completed appointment cannot be cancelled")
        return redirect("my_bookings")

    if booking.status == "Cancelled":
        messages.warning(request, "Already cancelled")
        return redirect("my_bookings")

    # ================= CANCEL =================
    booking.status = "Cancelled"
    booking.save()

    messages.success(request, "Booking cancelled successfully ✅")

    return redirect("my_bookings")



# ================= BOOK LAB ================= #
@login_required
def book_lab_test(request, lab_id):

    lab = get_object_or_404(Lab, id=lab_id)

    if request.method == "POST":
        LabAppointment.objects.create(
            user=request.user,
            lab=lab,
            test_name=request.POST.get("test"),
            status="Pending"
        )

        messages.success(request, "Lab test booked")
        return redirect("user_dashboard")

    return render(request, "UserPortal/book_lab.html", {"lab": lab})


# ================= LAB REPORTS ================= #


# ================= UPLOAD RECORD ================= #
@login_required
def patient_reports(request):

    patient = request.user

    # ================= UPLOAD LOGIC =================
    if request.method == "POST":

        file = request.FILES.get("file")

        if not file:
            messages.error(request, "Please select a file")
            return redirect("patient_reports")

        if file.size > 5 * 1024 * 1024:
            messages.error(request, "File too large (Max 5MB)")
            return redirect("patient_reports")

        allowed_types = ["application/pdf", "image/jpeg", "image/png"]

        if file.content_type not in allowed_types:
            messages.error(request, "Only PDF, JPG, PNG allowed")
            return redirect("patient_reports")

        MedicalRecord.objects.create(
            patient=patient,
            file=file
        )

        messages.success(request, "Record uploaded successfully ✅")
        return redirect("patient_reports")


    # ================= LAB REPORTS =================
    reports = LabAppointment.objects.filter(
        patient=patient,
        status="Completed"
    ).order_by("-appointment_date")


    # ================= UPLOADED RECORDS =================
    records = MedicalRecord.objects.filter(
        patient=patient
    ).order_by("-uploaded_at")


    # ================= DOCTOR PRESCRIPTIONS (🔥 FIXED) =================
    from django.db.models import Q

    doctor_prescriptions = Appointment.objects.filter(
        patient=patient
    ).filter(
        Q(prescription_file__isnull=False) |   # file upload
        Q(prescriptions__isnull=False)         # medicine added
    ).distinct().prefetch_related("prescriptions").order_by("-appointment_date")


    # ================= CONTEXT =================
    context = {
        "reports": reports,
        "records": records,
        "doctor_reports": doctor_prescriptions,  # 🔥 MATCH TEMPLATE
        "total_reports": reports.count(),
        "total_records": records.count(),
    }

    return render(request, "Patient/patient_reports.html", context)
# ================= PROFILE ================= #
@login_required
def user_profile(request):

    user = request.user
    patient = user.patient_profile   # 🔥 correct relation

    if request.method == "POST":

        # ===== PATIENT FIELDS =====
        patient.phone = request.POST.get("phone") or ""
        patient.address = request.POST.get("address") or ""

        patient.date_of_birth = request.POST.get("dob") or None
        patient.gender = request.POST.get("gender") or ""
        patient.blood_group = request.POST.get("blood_group") or ""

        patient.full_address = request.POST.get("full_address") or ""
        patient.pincode = request.POST.get("pincode") or ""
        patient.emergency_contact = request.POST.get("emergency_contact") or ""

        patient.allergies = request.POST.get("allergies") or ""
        patient.medical_conditions = request.POST.get("medical_conditions") or ""

        # IMAGE (OPTIONAL)
        if request.FILES.get("profile_image"):
            patient.profile_photo = request.FILES.get("profile_image")

        patient.save()

        return redirect("user_profile")

    return render(request, 'Patient/user_profile.html', {
        "user": user,
        "patient": patient
    })
# ================= PUBLIC LIST ================= #
def user_labs(request):
    labs = Lab.objects.filter(is_verified=True)
    return render(request, 'User/user_labs.html', {'labs': labs})


def user_doctors(request):
    doctors = Doctor.objects.filter(is_verified=True)
    return render(request, 'User/user_doctors.html', {'doctors': doctors})

@login_required
def user_appointments(request):
    return render(request, "Patient/appointments.html")

@login_required
def past_appointments(request):

    patient = request.user
    today = timezone.localdate()

    # ================= DOCTOR =================
    doctor_appointments = Appointment.objects.filter(
        patient=patient,
        appointment_date__lt=today
    ).exclude(status="Cancelled")

    # ================= LAB =================
    lab_appointments = LabAppointment.objects.filter(
        patient=patient,
        appointment_date__lt=today
    ).exclude(status="Cancelled")

    # ================= COMBINE =================
    all_appointments = []

    # Doctor data
    for a in doctor_appointments:
        all_appointments.append({
            "type": "Doctor",
            "name": a.doctor.name,
            "date": a.appointment_date,
            "time": a.appointment_time,
            "status": a.status
        })

    # Lab data
    for l in lab_appointments:
        all_appointments.append({
            "type": "Lab",
            "name": l.test_name,
            "date": l.appointment_date,
            "time": l.appointment_time,
            "status": l.status
        })

    # 🔥 SORT (latest first)
    all_appointments = sorted(
        all_appointments,
        key=lambda x: (x["date"], x["time"]),
        reverse=True
    )

    context = {
        "appointments": all_appointments
    }

    return render(request, "Patient/past_appointments.html", context)


# ================= FORGOT PASSWORD ================= #
def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        user = User.objects.filter(email__iexact=email, is_verified=True).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = _token_generator.make_token(user)
            reset_link = request.build_absolute_uri(f"/reset-password/{uid}/{token}/")
            try:
                send_password_reset_email(user.email, reset_link)
            except Exception:
                pass
        # Always show success to prevent email enumeration
        messages.success(request, "If that email is registered, a reset link has been sent.")
        return redirect("forgot_password")
    return render(request, "forgot_password.html")


# ================= RESET PASSWORD ================= #
def reset_password(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError):
        user = None

    if user is None or not _token_generator.check_token(user, token):
        messages.error(request, "This reset link is invalid or has expired.")
        return redirect("forgot_password")

    if request.method == "POST":
        password = request.POST.get("password", "")
        confirm = request.POST.get("confirm_password", "")
        if len(password) < 6:
            messages.error(request, "Password must be at least 6 characters.")
        elif password != confirm:
            messages.error(request, "Passwords do not match.")
        else:
            user.set_password(password)
            user.save()
            messages.success(request, "Password reset successful. Please log in.")
            return redirect("patient_login")

    return render(request, "reset_password.html", {"uidb64": uidb64, "token": token})