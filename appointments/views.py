from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import datetime, timedelta
from datetime import datetime, date

from .models import Appointment, Payment, LabAppointment
from .forms import AppointmentForm, LabAppointmentForm

from Doctor.models import Doctor, DoctorAvailability, LabAvailability
from Doctor.models import Lab, LabTest
from Doctor.LabViews import *


# =====================================================
# 🕒 GENERATE TIME SLOTS
# =====================================================

def generate_slots(start_time, end_time, duration):

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

    print("START:", start_time)
    print("END:", end_time)
    print("SLOTS:", slots)

    return slots


# =====================================================
# 📅 BOOK SLOT PAGE
# =====================================================

def book_slot(request, doctor_id):

    doctor = get_object_or_404(Doctor, id=doctor_id)

    today = datetime.today().date()
    today_day = today.strftime("%a")

    doctor_days_list = [d.strip() for d in (doctor.available_days or [])]

    if today_day not in doctor_days_list:

        return render(request, "appointments/doctor_not_available.html", {
            "doctor": doctor
        })

    availability = DoctorAvailability.objects.filter(
        doctor=doctor
    ).first()

    if availability and availability.is_available == False:

        return render(request, "appointments/doctor_not_available.html", {
            "doctor": doctor
        })

    start_time = doctor.start_time
    end_time = doctor.end_time
    duration = doctor.appointment_duration or 15

    slots = generate_slots(start_time, end_time, duration)

    booked_slots = Appointment.objects.filter(
        doctor=doctor,
        appointment_date=today,
        status__in=["Pending", "Approved"]
    ).values_list("appointment_time", flat=True)

    available_slots = [slot for slot in slots if slot not in booked_slots]

    print("TODAY:", today_day)
    print("DOCTOR DAYS:", doctor.available_days)
    print("TOGGLE:", availability.is_available if availability else "No Record")

    return render(request, "appointments/book_slot.html", {
        "doctor": doctor,
        "slots": available_slots,
        "today": today
    })


# =====================================================
# 📋 CONFIRM BOOKING
# =====================================================

# @login_required
# def confirm_booking(request, doctor_id, slot_time):

#     doctor = get_object_or_404(Doctor, id=doctor_id)

#     try:
#         slot_time_obj = datetime.strptime(slot_time, "%H:%M:%S").time()
#     except ValueError:
#         messages.error(request, "Invalid slot selected.")
#         return redirect("book_slot", doctor_id=doctor.id)

#     if request.method == "POST":

#         form = AppointmentForm(request.POST)

#         if form.is_valid():

#             appointment = form.save(commit=False)

#             appointment.doctor = doctor
#             appointment.patient = request.user
#             appointment.appointment_date = datetime.today().date()
#             appointment.appointment_time = slot_time_obj
#             appointment.payment_type = "Online"
#             appointment.status = "Pending"

#             appointment.save()

#             messages.success(request, "Appointment booked successfully!")

#             return redirect("home")

#         else:
#             messages.error(request, "Please correct the form errors.")

#     else:
#         form = AppointmentForm()

#     return render(request, "appointments/confirm_booking.html", {
#         "form": form,
#         "doctor": doctor,
#         "slot_time": slot_time_obj
#     })

@login_required
def confirm_booking(request, doctor_id, slot_time):

    doctor = get_object_or_404(Doctor, id=doctor_id)

    try:
        slot_time_obj = datetime.strptime(slot_time, "%H:%M:%S").time()
    except ValueError:
        messages.error(request, "Invalid slot selected.")
        return redirect("book_slot", doctor_id=doctor.id)

    # 🔥 ADD THIS
    consultation_fee = doctor.consultation_fee

    if request.method == "GET":
        form = AppointmentForm()

        return render(request, "appointments/confirm_booking.html", {
            "form": form,
            "doctor": doctor,
            "slot_time": slot_time_obj,
            "fee": consultation_fee   # ✅ PASS
        })

    if request.method == "POST":

        form = AppointmentForm(request.POST)

        if form.is_valid():

            appointment = form.save(commit=False)

            appointment.doctor = doctor
            appointment.patient = request.user
            appointment.appointment_date = datetime.today().date()
            appointment.appointment_time = slot_time_obj
            appointment.payment_type = "Online"
            appointment.status = "Pending"

            # 🔥 SAVE FEE IN APPOINTMENT (IMPORTANT)
            appointment.amount = consultation_fee

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
        "fee": consultation_fee
    })


# =====================================================
# 💳 PAYMENT PAGE
# =====================================================

@login_required
def payment_page(request, appointment_id):

    appointment = get_object_or_404(Appointment, id=appointment_id)

    if request.method == "POST":

        Payment.objects.create(
            user=request.user,
            appointment=appointment,
            amount=appointment.doctor.consultation_fee,
            payment_method=request.POST.get("payment_method"),
            status="Success"
        )

        appointment.is_paid = True
        appointment.save()

        return redirect("payment_success")

    context = {
        "appointment": appointment,
        "amount": appointment.doctor.consultation_fee
    }

    return render(request, "payment.html", context)


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

from datetime import datetime

def lab_book_slot(request, lab_id, test_id):

    lab = get_object_or_404(Lab, id=lab_id)
    test = get_object_or_404(LabTest, id=test_id)

    today = datetime.today().date()
    today_day_full = today.strftime("%A")   # Monday, Tuesday

    # 🔥 STEP 1: CHECK OPERATING DAYS
    lab_days = [d.strip() for d in (lab.operating_days or "").split(",") if d]

    if today_day_full not in lab_days:
        return render(request, "Lab/lab_closed.html", {
            "lab": lab,
            "message": "Lab is closed today"
        })

    # 🔥 STEP 2: CHECK TOGGLE (LAB AVAILABILITY)
    availability, created = LabAvailability.objects.get_or_create(lab=lab)

    if not availability.is_available:
        return render(request, "Lab/lab_closed.html", {
            "lab": lab,
            "message": "Lab is currently not accepting bookings"
        })

    # 🔥 STEP 3: GENERATE SLOTS
    start = lab.opening_time
    end = lab.closing_time
    duration = 15

    slots = generate_lab_slots(start, end, duration)

    # 🔥 STEP 4: REMOVE BOOKED SLOTS
    booked_slots = LabAppointment.objects.filter(
        lab=lab,
        appointment_date=today,
        status__in=["Pending", "Approved"]
    ).values_list("appointment_time", flat=True)

    available_slots = [
        slot for slot in slots if slot not in booked_slots
    ]

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

    # ================= TIME PARSE =================
    try:
        slot_time_obj = datetime.strptime(slot_time, "%H:%M:%S").time()
    except ValueError:
        messages.error(request, "Invalid slot selected.")
        return redirect("lab_book_slot", lab_id=lab.id)

    # ================= TEST NAME + PRICE =================
    test_name = lab_test.get_name()   # 🔥 FINAL FIX
    test_price = lab_test.price       # 🔥 PRICE ADD

    # ================= POST =================
    if request.method == "POST":

        full_name = request.POST.get("full_name")
        age = request.POST.get("age")
        gender = request.POST.get("gender")
        contact_number = request.POST.get("contact_number")
        email = request.POST.get("email")
        address = request.POST.get("address")

        # ================= VALIDATION =================
        if not all([full_name, age, gender, contact_number, email]):
            messages.error(request, "Please fill all required fields.")
            return redirect(request.path)

        # ================= SAVE =================
        appointment = LabAppointment.objects.create(
            full_name=full_name,
            age=age,
            gender=gender,
            contact_number=contact_number,
            email=email,
            address=address,

            test_name=test_name,     # ✅ CORRECT NAME
            test_price=test_price,   # ✅ PRICE ADD

            lab=lab,
            patient=request.user,
            appointment_date=date.today(),
            appointment_time=slot_time_obj,
            status="Pending"
        )

        # ================= SUCCESS =================
        return render(request, "Lab/booking_success.html", {
            "appointment": appointment
        })

    # ================= GET =================
    return render(request, "Lab/confirm_booking.html", {
        "lab": lab,
        "test": lab_test,
        "slot_time": slot_time,
        "test_name": test_name,
        "test_price": test_price   # 🔥 SHOW PRICE
    })