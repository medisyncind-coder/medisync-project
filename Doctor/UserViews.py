from django.shortcuts import render
from .models import Appointment, Doctor, Lab


# ---------------- USER HOME ---------------- #
def user_home(request):
    return render(request, 'User/user_home.html')


# ---------------- USER PROFILE ---------------- #
def user_profile(request):
    return render(request, 'User/user_profile.html')


# ---------------- USER APPOINTMENTS ---------------- #
def user_appointments(request):
    appointments = Appointment.objects.all()
    return render(request, 'User/user_appointments.html', {
        'appointments': appointments
    })


# ---------------- USER LABS ---------------- #
def user_labs(request):
    labs = Lab.objects.filter(is_verified=True)
    return render(request, 'User/user_labs.html', {'labs': labs})


# ---------------- USER DOCTORS ---------------- #
def user_doctors(request):
    doctors = Doctor.objects.filter(is_verified=True)
    return render(request, 'User/user_doctors.html', {'doctors': doctors})
