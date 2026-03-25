
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import random
from accounts.models import *
from accounts.emails import send_otp_via_email
from .forms import LabRegistrationForm, LabTestFormSet
from .models import (
    Lab,
    LabTest,
    LabAppointment,
    LabReport,
    LabWorkingHours,
    LabAvailability,
    Test
)

# ======================================================
# OTP GENERATOR
# ======================================================

def generate_otp():
    return str(random.randint(100000, 999999))


# ======================================================
# PUBLIC LAB LIST
# ======================================================

def lab_list(request):

    labs = Lab.objects.filter(is_verified=True)

    search = request.GET.get("search")
    city = request.GET.get("city")

    if search:
        labs = labs.filter(lab_name__icontains=search)

    if city:
        labs = labs.filter(city__icontains=city)

    cities = Lab.objects.values_list("city", flat=True).distinct()

    return render(request, "Lab/lab_list.html", {
        "labs": labs,
        "cities": cities
    })


# ======================================================
# LAB DETAIL PAGE
# ======================================================

def lab_detail(request, lab_id):

    lab = get_object_or_404(Lab, id=lab_id, is_verified=True)

    tests = LabTest.objects.filter(
        lab=lab
    ).select_related("test").order_by("test__name")

    context = {
        "lab": lab,
        "tests": tests,
        "total_tests": tests.count(),
        "home_collection": lab.home_sample_collection,
        "opening_time": lab.opening_time,
        "closing_time": lab.closing_time,
        "operating_days": lab.operating_days
    }

    return render(request, "Lab/lab_detail.html", context)

def view_lab_tests(request, lab_id):

    lab = get_object_or_404(Lab, id=lab_id)

    tests = LabTest.objects.filter(lab=lab)

    return render(request, "Lab/view_lab_tests.html", {
        "lab": lab,
        "tests": tests
    })
    
@login_required
def lab_bookings(request):

    lab = get_object_or_404(Lab, user=request.user)

    appointments = LabAppointment.objects.filter(
        lab=lab
    ).order_by("-created_at")

    return render(request, "LabPortal/lab_bookings.html", {
        "appointments": appointments
    })


# ======================================================
# LAB REGISTRATION
# ======================================================

def lab_registration(request):

    if request.method == "POST":

        form = LabRegistrationForm(request.POST, request.FILES)

        if form.is_valid():

            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]

            try:

                with transaction.atomic():

                    if User.objects.filter(email__iexact=email).exists():
                        messages.error(request, "Email already registered")
                        return redirect("lab_registration")

                    user = User.objects.create_user(
                        email=email,
                        password=password
                    )

                    user.is_verified = False

                    otp = generate_otp()
                    user.otp = otp
                    user.save()

                    send_otp_via_email(user.email, otp, role="Lab")

                    lab = form.save(commit=False)
                    lab.user = user
                    lab.is_verified = False
                    lab.save()

                    # SAVE TESTS
                    test_ids = request.POST.getlist("test_id[]")
                    test_prices = request.POST.getlist("test_price[]")

                    for test_id, price in zip(test_ids, test_prices):

                        if test_id and price:

                            LabTest.objects.create(
                                lab=lab,
                                test_id=test_id,
                                price=price
                            )

                    # SAVE CUSTOM TESTS
                    custom_names = request.POST.getlist("custom_test_name[]")
                    custom_prices = request.POST.getlist("custom_test_price[]")

                    for name, price in zip(custom_names, custom_prices):

                        if name and price:

                            test = Test.objects.create(name=name)

                            LabTest.objects.create(
                                lab=lab,
                                test=test,
                                price=price
                            )

                    request.session["lab_email"] = user.email

                    messages.success(request, "OTP sent to your email")

                    return redirect("verify_lab_otp")

            except Exception as e:

                print("LAB REGISTER ERROR:", e)
                messages.error(request, "Registration failed")

    else:

        form = LabRegistrationForm()

    return render(request, "Lab/lab_registration.html", {
        "form": form,
        "tests": Test.objects.all()
    })


# ======================================================
# VERIFY OTP
# ======================================================

def verify_lab_otp(request):

    email = request.session.get("lab_email")

    if not email:
        return redirect("lab_registration")

    user = get_object_or_404(User, email=email)
    lab = get_object_or_404(Lab, user=user)

    if request.method == "POST":

        otp = request.POST.get("otp")

        if user.otp and user.otp == otp:

            # ✅ verify user
            user.is_verified = True
            user.otp = None
            user.save()

            # ✅ verify lab
            lab.is_verified = True
            lab.save()

            # 🔥 LOGIN KARO
            login(request, user)

            # 🧹 session clean
            request.session.pop("lab_email", None)

            messages.success(request, "Lab verified & logged in successfully")

            # 🚀 DIRECT DASHBOARD
            return redirect("LabPortal/lab_dashboard.html")

        else:
            messages.error(request, "Invalid OTP")

    return render(request, "Lab/verify_lab_otp.html", {
        "lab": lab
    })


# ======================================================
# LAB LOGIN
# ======================================================

def lab_login(request):

    if request.user.is_authenticated:

        try:
            Lab.objects.get(user=request.user)
            return redirect("lab_dashboard")

        except Lab.DoesNotExist:
            logout(request)

    return render(request, "Lab/lab_login.html")


def do_lab_login(request):

    if request.method == "POST":

        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, email=email, password=password)

        if user is None:
            messages.error(request, "Invalid credentials")
            return redirect("lab_login")

        if not user.is_verified:
            messages.error(request, "Please verify OTP first")
            return redirect("lab_login")

        if not Lab.objects.filter(user=user).exists():
            messages.error(request, "This is not a Lab account")
            return redirect("lab_login")

        login(request, user)

        return redirect("lab_dashboard")

    return redirect("lab_login")


# ======================================================
# LAB DASHBOARD
# ======================================================

@login_required
def lab_dashboard(request):

    lab = Lab.objects.filter(user=request.user).first()

    if not lab:
        messages.error(request, "Lab profile not found.")
        return redirect("home")

    today = timezone.now().date()

    appointments = LabAppointment.objects.filter(lab=lab)

    context = {

        "total_appointments": appointments.count(),

        "pending_appointments": appointments.filter(status="Pending").count(),

        "completed_appointments": appointments.filter(status="Completed").count(),

        "recent_appointments": appointments.order_by("-created_at")[:10],

        "total_reports": LabReport.objects.filter(
            appointment__lab=lab
        ).count()
    }

    return render(request, "LabPortal/lab_dashboard.html", context)

# ======================================================
# LAB APPOINTMENTS
# ======================================================

@login_required
def lab_appointments(request):

    lab = get_object_or_404(Lab, user=request.user)

    appointments = LabAppointment.objects.filter(
        lab=lab
    ).order_by("-created_at")

    return render(request, "LabPortal/lab_appointments.html", {
        "appointments": appointments
    })

@login_required
def add_lab_tests(request):

    lab = get_object_or_404(Lab, user=request.user)

    if request.method == "POST":

        test_ids = request.POST.getlist("test_id[]")
        custom_names = request.POST.getlist("custom_name[]")
        descriptions = request.POST.getlist("description[]")
        prices = request.POST.getlist("price[]")

        for i in range(len(prices)):

            if not prices[i]:
                continue

            test_id = test_ids[i]
            custom_name = custom_names[i]
            description = descriptions[i]
            price = prices[i]

            # 🔹 Case 1: Existing predefined test selected
            if test_id:
                existing_test = LabTest.objects.filter(
                    lab=lab,
                    test_id=test_id
                ).first()

                if existing_test:
                    existing_test.price = price
                    existing_test.is_active = True
                    existing_test.save()
                else:
                    LabTest.objects.create(
                        lab=lab,
                        test_id=test_id,
                        price=price
                    )

            # 🔹 Case 2: Custom test added
            elif custom_name:
                LabTest.objects.create(
                    lab=lab,
                    custom_name=custom_name,
                    description=description,
                    price=price,
                    is_active=True
                )

        messages.success(request, "Tests added/updated successfully")
        return redirect("lab_dashboard")

    return redirect("lab_dashboard")

# ======================================================
# APPROVE / REJECT / COMPLETE
# ======================================================

@login_required
def approve_lab_appointment(request, appointment_id):

    lab = get_object_or_404(Lab, user=request.user)
    appointment = get_object_or_404(LabAppointment, id=appointment_id, lab=lab)

    appointment.status = "Approved"
    appointment.save()

    messages.success(request, "✅ Test Approved Successfully")

    return redirect("lab_bookings")   # ✅ FIXED


# =========================
# REJECT APPOINTMENT
# =========================
@login_required
def reject_lab_appointment(request, appointment_id):

    lab = get_object_or_404(Lab, user=request.user)
    appointment = get_object_or_404(LabAppointment, id=appointment_id, lab=lab)

    appointment.status = "Cancelled"
    appointment.save()

    messages.error(request, "❌ Test Rejected")

    return redirect("lab_bookings")   # ✅ FIXED


# =========================
# COMPLETE APPOINTMENT
# =========================
@login_required
def complete_lab_appointment(request, appointment_id):

    lab = get_object_or_404(Lab, user=request.user)
    appointment = get_object_or_404(LabAppointment, id=appointment_id, lab=lab)

    appointment.status = "Completed"
    appointment.save()

    messages.success(request, "🎉 Test Completed")

    return redirect("lab_bookings")   # ✅ FIXED


# ======================================================
# REPORT SYSTEM
# ======================================================

@login_required
def lab_reports(request):
    appointments = LabAppointment.objects.filter(
        lab__user=request.user
    ).order_by("-created_at")

    return render(request, "LabPortal/lab_reports.html", {
        "appointments": appointments
    })

@login_required
def upload_lab_report(request, appointment_id):

    lab = get_object_or_404(Lab, user=request.user)

    appointment = get_object_or_404(
        LabAppointment,
        id=appointment_id,
        lab=lab
    )

    if appointment.status != "Completed":
        messages.error(request, "Report can only be uploaded after completion")
        return redirect("lab_reports")

    if request.method == "POST":

        report_file = request.FILES.get("report_file")

        if report_file:
            # 🔥 DIRECT SAVE (IMPORTANT)
            appointment.report_file = report_file
            appointment.save()

            messages.success(request, "✅ Report uploaded successfully")
            return redirect("lab_reports")

    return render(request, "LabPortal/upload_report.html", {
        "appointment": appointment
    })
# ======================================================
# LAB SERVICES
# ======================================================

@login_required
def lab_services(request):

    lab = get_object_or_404(Lab, user=request.user)

    services = LabTest.objects.filter(lab=lab)

    return render(request, "LabPortal/lab_services.html", {
        "services": services
    })


# ======================================================
# LAB PROFILE
# ======================================================

@login_required
def lab_profile(request):

    lab = get_object_or_404(Lab, user=request.user)

    return render(request, "LabPortal/lab_profile.html", {
        "lab": lab
    })


# ======================================================
# LAB WORKING HOURS
# ======================================================
@login_required
def lab_edit_profile(request):
    lab = Lab.objects.get(user=request.user)

    if request.method == "POST":
        lab.address = request.POST.get("address")
        lab.contact_number = request.POST.get("contact")
        lab.opening_time = request.POST.get("opening_time")
        lab.closing_time = request.POST.get("closing_time")
        lab.average_report_time = request.POST.get("report_time")

        lab.save()

        messages.success(request, "Profile Updated Successfully")
        return redirect("lab_edit_profile")

    # all tests
    lab_tests = LabTest.objects.filter(lab=lab)

    all_tests = Test.objects.all()

    return render(request, "LabPortal/lab_edit_profile.html", {
        "lab": lab,
        "lab_tests": lab_tests,
        "all_tests": all_tests
    })


# ======================================================
# LAB AVAILABILITY
# ======================================================

@login_required
def lab_availability(request):

    lab = get_object_or_404(Lab, user=request.user)

    availability, created = LabAvailability.objects.get_or_create(lab=lab)

    return render(request,"LabPortal/lab_availability.html",{
        "lab":lab,
        "availability":availability
    })


@login_required
def toggle_lab_availability(request):

    lab = get_object_or_404(Lab, user=request.user)

    availability, created = LabAvailability.objects.get_or_create(lab=lab)

    availability.is_available = not availability.is_available
    availability.save()

    msg = "Lab is now OPEN for bookings" if availability.is_available else "Lab is CLOSED for bookings"
    messages.success(request, msg)

    return redirect("lab_availability")


# ======================================================
# LOGOUT
# ======================================================

def lab_logout(request):

    logout(request)

    messages.success(request, "Logged out successfully")

    return redirect("home")


# ======================================================
# SUCCESS PAGE
# ======================================================

def lab_success(request):

    return render(request, "Lab/lab_success.html")

@login_required
def toggle_test(request, id):

    lab_test = get_object_or_404(LabTest, id=id)

    # security check
    if lab_test.lab.user != request.user:
        return redirect("lab_dashboard")

    lab_test.is_active = not lab_test.is_active
    lab_test.save()

    return redirect("lab_edit_profile")


@login_required
def update_test_price(request, id):

    lab_test = get_object_or_404(LabTest, id=id)

    if lab_test.lab.user != request.user:
        return redirect("lab_dashboard")

    if request.method == "POST":
        price = request.POST.get("price")
        lab_test.price = price
        lab_test.save()

    return redirect("lab_edit_profile")