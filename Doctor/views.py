from django.shortcuts import render
from Doctor.models import Doctor, Lab, Patient
from appointments.models import Appointment

# ---------------- HOME / COMMON ---------------- #

def home(request):
    context = {
        "total_doctors": Doctor.objects.filter(user__is_verified=True).count(),
        "total_labs": Lab.objects.count(),
        "total_appointments": Appointment.objects.count(),
        "total_patients": Patient.objects.count(),
    }
    return render(request, 'index.html', context)
