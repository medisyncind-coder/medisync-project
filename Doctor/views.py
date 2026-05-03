from django.shortcuts import render
from django.core.cache import cache
from Doctor.models import Doctor, Lab, Patient
from appointments.models import Appointment

# ---------------- HOME / COMMON ---------------- #

def home(request):
    stats = cache.get('home_stats')
    if not stats:
        stats = {
            "total_doctors": Doctor.objects.filter(user__is_verified=True).count(),
            "total_labs": Lab.objects.count(),
            "total_appointments": Appointment.objects.count(),
            "total_patients": Patient.objects.count(),
        }
        cache.set('home_stats', stats, 300)  # cache for 5 minutes
    return render(request, 'index.html', stats)
