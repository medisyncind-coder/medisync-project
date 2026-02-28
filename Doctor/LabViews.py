from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
import random

from accounts.models import User
from accounts.emails import send_otp_via_email

from .forms import LabRegistrationForm, LabTestFormSet
from .models import Lab, LabTest, LabAppointment, LabReport


# ======================================================
# 🔢 OTP GENERATOR
# ======================================================
def generate_otp():
    return str(random.randint(100000, 999999))


# ======================================================
# 🏥 LAB LIST (PUBLIC)
# ======================================================
def lab_list(request):
    labs = Lab.objects.filter(is_verified=True)
    return render(request, 'Lab/lab_list.html', {'labs': labs})


# ======================================================
# 🏥 LAB REGISTER
# ======================================================
def lab_registration(request):

    if request.method == "POST":
        form = LabRegistrationForm(request.POST, request.FILES)

        if form.is_valid():

            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            try:
                with transaction.atomic():

                    if User.objects.filter(email__iexact=email).exists():
                        messages.error(request, "Email already registered")
                        return render(request, 'Lab/lab_registration.html', {'form': form})

                    # Create User
                    user = User.objects.create_user(
                        email=email,
                        password=password
                    )
                    user.is_verified = False

                    otp = generate_otp()
                    user.otp = otp
                    user.save()

                    send_otp_via_email(user.email, otp, role="Lab")

                    # Create Lab Profile
                    lab = form.save(commit=False)
                    lab.user = user
                    lab.is_verified = False
                    lab.save()

                    request.session['lab_email'] = user.email

                    return redirect('verify_lab_otp')

            except Exception as e:
                print("❌ LAB REGISTER ERROR:", e)
                messages.error(request, "Registration failed")

        else:
            messages.error(request, "Invalid form data")

    else:
        form = LabRegistrationForm()

    return render(request, 'Lab/lab_registration.html', {'form': form})


# ======================================================
# 🔒 VERIFY LAB OTP
# ======================================================
def verify_lab_otp(request):

    email = request.session.get('lab_email')

    if not email:
        return redirect('lab_registration')

    user = get_object_or_404(User, email=email)
    lab = get_object_or_404(Lab, user=user)

    if request.method == "POST":
        otp = request.POST.get('otp')

        if user.otp and user.otp == otp:

            user.is_verified = True
            user.otp = None
            user.save()

            lab.is_verified = True
            lab.save()

            request.session.pop('lab_email', None)

            messages.success(request, "Lab verified successfully. Please login.")
            return redirect('lab_login')

        else:
            messages.error(request, "Invalid OTP")

    return render(request, 'Lab/verify_lab_otp.html', {'lab': lab})


# ======================================================
# 🧪 ADD LAB TESTS
# ======================================================
@login_required
def add_lab_tests(request):

    lab = get_object_or_404(Lab, user=request.user)

    if request.method == 'POST':
        formset = LabTestFormSet(
            request.POST,
            request.FILES,
            queryset=LabTest.objects.none()
        )

        if formset.is_valid():
            for form in formset:
                if form.cleaned_data:
                    form.save(lab=lab)

            messages.success(request, "Tests added successfully")
            return redirect('lab_dashboard')

    else:
        formset = LabTestFormSet(queryset=LabTest.objects.none())

    return render(request, 'Lab/add_lab_tests.html', {
        'formset': formset,
        'lab': lab
    })


# ======================================================
# 🏥 LAB OWNER DASHBOARD
# ======================================================
@login_required
def lab_dashboard(request):

    lab = get_object_or_404(Lab, user=request.user)

    appointments = LabAppointment.objects.filter(
        lab=lab
    ).order_by('-created_at')

    total_tests = LabTest.objects.filter(lab=lab).count()
    total_appointments = appointments.count()
    pending_appointments = appointments.filter(status="Pending").count()
    completed_appointments = appointments.filter(status="Completed").count()

    return render(request, 'Lab/lab_dashboard.html', {
        'lab': lab,
        'appointments': appointments,
        'total_tests': total_tests,
        'total_appointments': total_appointments,
        'pending_appointments': pending_appointments,
        'completed_appointments': completed_appointments,
    })


# ======================================================
# ✅ APPROVE APPOINTMENT
# ======================================================
@login_required
def approve_lab_appointment(request, appointment_id):

    appointment = get_object_or_404(
        LabAppointment,
        id=appointment_id,
        lab__user=request.user
    )

    appointment.status = "Approved"
    appointment.save()

    messages.success(request, "Appointment Approved")
    return redirect('lab_dashboard')


# ======================================================
# 📤 UPLOAD LAB REPORT
# ======================================================
@login_required
def upload_lab_report(request, appointment_id):

    appointment = get_object_or_404(
        LabAppointment,
        id=appointment_id,
        lab__user=request.user
    )

    if request.method == "POST":
        report_file = request.FILES.get("report_file")
        remarks = request.POST.get("remarks")

        LabReport.objects.update_or_create(
            appointment=appointment,
            defaults={
                'report_file': report_file,
                'remarks': remarks
            }
        )

        appointment.status = "Completed"
        appointment.save()

        messages.success(request, "Report uploaded successfully")
        return redirect('lab_dashboard')

    return render(request, 'Lab/upload_report.html', {
        'appointment': appointment
    })


# ======================================================
# 🔑 LAB LOGIN
# ======================================================

def lab_login(request):

    # Agar already login hai aur lab account hai
    if request.user.is_authenticated:
        try:
            Lab.objects.get(user=request.user)
            return redirect('lab_dashboard')
        except Lab.DoesNotExist:
            logout(request)

    return render(request, 'Lab/lab_login.html')


# ===============================
# 🔑 LAB LOGIN SUBMIT
# ===============================
def do_lab_login(request):

    if request.method == "POST":

        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, email=email, password=password)

        if user is None:
            messages.error(request, "Invalid credentials")
            return redirect('lab_login')

        if not user.is_verified:
            messages.error(request, "Please verify OTP first")
            return redirect('lab_login')

        # Check if user is Lab
        try:
            Lab.objects.get(user=user)
        except Lab.DoesNotExist:
            messages.error(request, "This is not a Lab account")
            return redirect('lab_login')

        login(request, user)
        return redirect('lab_dashboard')

    return redirect('lab_login')


# ======================================================
# 🚪 LOGOUT
# ======================================================
def lab_logout(request):
    logout(request)
    messages.success(request, "Logged out successfully")
    return redirect('home')


# ======================================================
# 🔬 VIEW LAB TESTS (PUBLIC)
# ======================================================
def view_lab_tests(request, lab_id):
    lab = get_object_or_404(Lab, id=lab_id)
    tests = LabTest.objects.filter(lab=lab)

    return render(request, 'Lab/view_lab_tests.html', {
        'lab': lab,
        'tests': tests
    })
    
    
# ======================================================
# 🎉 LAB SUCCESS PAGE
# ======================================================

def lab_success(request):
    return render(request, 'Lab/lab_success.html')