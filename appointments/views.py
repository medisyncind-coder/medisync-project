from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import datetime, timedelta, date

from .models import Appointment, Payment, LabAppointment
from .forms import AppointmentForm, LabAppointmentForm

from Doctor.models import Doctor, DoctorAvailability, LabAvailability
from Doctor.models import Lab, LabTest
from Doctor.LabViews import *


# =====================================================
# 🕒 GENERATE TIME SLOTS
# =====================================================

def generate_slots(start_time, end_time, duration, for_date=None):
    slots = []
    if not start_time or not end_time:
        return slots

    target_date = for_date or datetime.today().date()
    now = datetime.now()

    current = datetime.combine(target_date, start_time)
    end_dt = datetime.combine(target_date, end_time)

    while current < end_dt:
        if current > now:
            slots.append(current.time())
        current += timedelta(minutes=duration)

    return slots


# =====================================================
# 📅 BOOK SLOT PAGE
# =====================================================

def book_slot(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)

    today = datetime.today().date()
    doctor_days_list = [d.strip() for d in (doctor.available_days or [])]

    # Build the list of selectable dates (next 30 days matching doctor's schedule)
    available_dates = []
    for i in range(30):
        d = today + timedelta(days=i)
        if d.strftime("%a") in doctor_days_list:
            available_dates.append(d)

    # Resolve selected date from GET param, default to first available date
    selected_date = today
    date_str = request.GET.get("date")
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            selected_date = today

    # Validate selected date is actually an available day
    if selected_date.strftime("%a") not in doctor_days_list:
        selected_date = available_dates[0] if available_dates else today

    # Check doctor availability toggle
    availability = DoctorAvailability.objects.filter(doctor=doctor).first()
    if availability and not availability.is_available:
        return render(request, "appointments/doctor_not_available.html", {"doctor": doctor})

    if not available_dates:
        return render(request, "appointments/doctor_not_available.html", {"doctor": doctor})

    duration = doctor.appointment_duration or 15
    slots = generate_slots(doctor.start_time, doctor.end_time, duration, for_date=selected_date)

    booked_slots = Appointment.objects.filter(
        doctor=doctor,
        appointment_date=selected_date,
        status__in=["Pending", "Approved"]
    ).values_list("appointment_time", flat=True)

    available_slots = [slot for slot in slots if slot not in booked_slots]

    return render(request, "appointments/book_slot.html", {
        "doctor": doctor,
        "slots": available_slots,
        "selected_date": selected_date,
        "available_dates": available_dates,
        "today": today,
    })


# =====================================================
# 📋 CONFIRM BOOKING
# =====================================================

@login_required
def confirm_booking(request, doctor_id, booking_date, slot_time):

    doctor = get_object_or_404(Doctor, id=doctor_id)

    try:
        slot_time_obj = datetime.strptime(slot_time, "%H:%M:%S").time()
    except ValueError:
        messages.error(request, "Invalid slot selected.")
        return redirect("book_slot", doctor_id=doctor.id)

    try:
        appointment_date = datetime.strptime(booking_date, "%Y-%m-%d").date()
    except ValueError:
        messages.error(request, "Invalid date selected.")
        return redirect("book_slot", doctor_id=doctor.id)

    # Reject past dates
    if appointment_date < datetime.today().date():
        messages.error(request, "Cannot book appointments for past dates.")
        return redirect("book_slot", doctor_id=doctor.id)

    consultation_fee = doctor.consultation_fee

    if request.method == "GET":
        form = AppointmentForm()
        return render(request, "appointments/confirm_booking.html", {
            "form": form,
            "doctor": doctor,
            "slot_time": slot_time_obj,
            "appointment_date": appointment_date,
            "fee": consultation_fee,
        })

    if request.method == "POST":
        form = AppointmentForm(request.POST)

        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.doctor = doctor
            appointment.patient = request.user
            appointment.appointment_date = appointment_date
            appointment.appointment_time = slot_time_obj
            appointment.payment_type = "Online"
            appointment.status = "Pending"
            appointment.save()

            return render(request, "appointments/booking_success.html", {
                "appointment": appointment
            })
        else:
            messages.error(request, "Please correct the form errors.")

    return render(request, "appointments/confirm_booking.html", {
        "form": form,
        "doctor": doctor,
        "slot_time": slot_time_obj,
        "appointment_date": appointment_date,
        "fee": consultation_fee,
    })


# =====================================================
# 💳 PAYMENT PAGE  (Razorpay)
# =====================================================

import razorpay
import hmac
import hashlib
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

@login_required
def payment_page(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user)

    if appointment.is_paid:
        return redirect("payment_success")

    amount_paise = int(appointment.doctor.consultation_fee * 100)

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    razorpay_order = client.order.create({
        "amount": amount_paise,
        "currency": "INR",
        "payment_capture": 1,
        "notes": {
            "appointment_id": str(appointment.id),
            "booking_id": appointment.booking_id,
        }
    })

    # Store pending payment record
    payment, _ = Payment.objects.get_or_create(
        appointment=appointment,
        defaults={
            "user": request.user,
            "amount": appointment.doctor.consultation_fee,
            "status": "Pending",
        }
    )
    payment.razorpay_order_id = razorpay_order["id"]
    payment.save()

    return render(request, "appointments/payment.html", {
        "appointment": appointment,
        "amount": appointment.doctor.consultation_fee,
        "amount_paise": amount_paise,
        "razorpay_order_id": razorpay_order["id"],
        "razorpay_key_id": settings.RAZORPAY_KEY_ID,
    })


# =====================================================
# 🔐 RAZORPAY CALLBACK (signature verification)
# =====================================================

@csrf_exempt
def razorpay_callback(request):
    if request.method != "POST":
        return redirect("home")

    razorpay_payment_id = request.POST.get("razorpay_payment_id", "")
    razorpay_order_id   = request.POST.get("razorpay_order_id", "")
    razorpay_signature  = request.POST.get("razorpay_signature", "")

    # Verify signature
    body = f"{razorpay_order_id}|{razorpay_payment_id}"
    expected = hmac.new(
        key=settings.RAZORPAY_KEY_SECRET.encode(),
        msg=body.encode(),
        digestmod=hashlib.sha256
    ).hexdigest()

    payment = Payment.objects.filter(razorpay_order_id=razorpay_order_id).first()
    if not payment:
        return render(request, "appointments/payment_failed.html")

    if hmac.compare_digest(expected, razorpay_signature):
        payment.razorpay_payment_id = razorpay_payment_id
        payment.status = "Success"
        payment.save()
        payment.appointment.is_paid = True
        payment.appointment.save()
        return redirect("payment_success")
    else:
        payment.status = "Failed"
        payment.save()
        return render(request, "appointments/payment_failed.html")


# =====================================================
# ✅ PAYMENT SUCCESS PAGE
# =====================================================

def payment_success(request):
    return render(request, "payment_success.html")


# =====================================================
# 🕒 GENERATE LAB SLOTS
# =====================================================

def generate_lab_slots(start_time, end_time, duration):

    slots = []

    if not start_time or not end_time:
        return slots

    today = datetime.today().date()
    now = datetime.now()

    current = datetime.combine(today, start_time)
    end = datetime.combine(today, end_time)

    while current < end:
        if current > now:
            slots.append(current.time())
        current += timedelta(minutes=duration)

    return slots


# =====================================================
# 🧪 LAB BOOK SLOT PAGE
# =====================================================

def lab_book_slot(request, lab_id, test_id):

    lab = get_object_or_404(Lab, id=lab_id)
    test = get_object_or_404(LabTest, id=test_id)

    today = datetime.today().date()
    today_day_full = today.strftime("%A")

    lab_days = [d.strip() for d in (lab.operating_days or "").split(",") if d]

    if today_day_full not in lab_days:
        return render(request, "Lab/lab_closed.html", {
            "lab": lab,
            "message": "Lab is closed today"
        })

    availability, created = LabAvailability.objects.get_or_create(lab=lab)

    if not availability.is_available:
        return render(request, "Lab/lab_closed.html", {
            "lab": lab,
            "message": "Lab is currently not accepting bookings"
        })

    slots = generate_lab_slots(lab.opening_time, lab.closing_time, 15)

    booked_slots = LabAppointment.objects.filter(
        lab=lab,
        appointment_date=today,
        status__in=["Pending", "Approved"]
    ).values_list("appointment_time", flat=True)

    available_slots = [slot for slot in slots if slot not in booked_slots]

    return render(request, "Lab/book_slot.html", {
        "lab": lab,
        "test": test,
        "slots": available_slots,
        "today": today
    })


# =====================================================
# 📋 CONFIRM LAB BOOKING
# =====================================================

@login_required
def confirm_lab_booking(request, lab_id, test_id, slot_time):

    lab = get_object_or_404(Lab, id=lab_id)
    lab_test = get_object_or_404(LabTest, id=test_id)

    try:
        slot_time_obj = datetime.strptime(slot_time, "%H:%M:%S").time()
    except ValueError:
        messages.error(request, "Invalid slot selected.")
        return redirect("lab_book_slot", lab_id=lab.id)

    test_name = lab_test.get_name()
    test_price = lab_test.price

    if request.method == "POST":
        full_name = request.POST.get("full_name")
        age = request.POST.get("age")
        gender = request.POST.get("gender")
        contact_number = request.POST.get("contact_number")
        email = request.POST.get("email")
        address = request.POST.get("address")

        if not all([full_name, age, gender, contact_number, email]):
            messages.error(request, "Please fill all required fields.")
            return redirect(request.path)

        appointment = LabAppointment.objects.create(
            full_name=full_name,
            age=age,
            gender=gender,
            contact_number=contact_number,
            email=email,
            address=address,
            test_name=test_name,
            test_price=test_price,
            lab=lab,
            patient=request.user,
            appointment_date=date.today(),
            appointment_time=slot_time_obj,
            status="Pending"
        )

        return render(request, "Lab/booking_success.html", {
            "appointment": appointment
        })

    return render(request, "Lab/confirm_booking.html", {
        "lab": lab,
        "test": lab_test,
        "slot_time": slot_time,
        "test_name": test_name,
        "test_price": test_price
    })
