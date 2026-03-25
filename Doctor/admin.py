from django.contrib import admin
from django.utils import timezone

# =========================
# IMPORT MODELS
# =========================
from accounts.models import *

from Doctor.models import *

from appointments.models import *
from Doctor.models import Patient, Doctor, Lab


# =========================
# 🔥 FIX USER DOUBLE REGISTER
# =========================
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

class PatientInline(admin.StackedInline):
    model = Patient
    extra = 0


class DoctorInline(admin.StackedInline):
    model = Doctor
    extra = 0


class LabInline(admin.TabularInline):   # FK hai
    model = Lab
    extra = 0

# =========================
# 🔥 USER ADMIN (FULL DETAIL FIX)
# =========================
@admin.register(User)
class UserAdmin(admin.ModelAdmin):

    list_display = ("id", "email", "is_verified", "is_staff", "is_superuser")
    list_filter = ("is_verified", "is_staff", "is_superuser")
    search_fields = ("email",)
    ordering = ("-id",)

    # 🔥 SAB DATA EK PAGE ME
    inlines = [
        PatientInline,
        DoctorInline,
        LabInline
    ]

    fieldsets = (

        ("🔐 Login Info", {
            "fields": ("email", "password")
        }),

        ("👤 Personal Info", {
            "fields": ("first_name", "last_name")
        }),

        ("📱 Verification", {
            "fields": ("is_verified", "otp")
        }),

        ("⚙️ Permissions", {
            "fields": ("is_staff", "is_superuser")
        }),

        ("🕒 Dates", {
            "fields": ("last_login", "date_joined")
        }),
    )

    readonly_fields = ("last_login", "date_joined")

    actions = ["verify_users"]

    def verify_users(self, request, queryset):
        queryset.update(is_verified=True)

# =========================
# PATIENT ADMIN
# =========================
@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "user", "phone", "gender")
    search_fields = ("name", "user__email")


# =========================
# MEDICAL RECORD ADMIN
# =========================
@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "uploaded_at")


# =========================
# DOCTOR ADMIN
# =========================
@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "specialization",
        "experience",
        "consultation_fee",
        "consultation_type"
    )
    search_fields = ("name", "specialization")
    list_filter = ("consultation_type",)


# =========================
# DOCTOR AVAILABILITY
# =========================
@admin.register(DoctorAvailability)
class DoctorAvailabilityAdmin(admin.ModelAdmin):
    list_display = ("doctor", "is_available", "updated_at")
    list_editable = ("is_available",)


# =========================
# LAB ADMIN
# =========================
@admin.register(Lab)
class LabAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "lab_name",
        "city",
        "lab_type",
        "is_verified",
        "home_sample_collection"
    )
    list_filter = ("city", "lab_type", "is_verified")
    search_fields = ("lab_name", "city", "email")

    readonly_fields = ("otp", "otp_created_at")

    actions = ["verify_labs"]

    def verify_labs(self, request, queryset):
        queryset.update(is_verified=True)


# =========================
# TEST ADMIN
# =========================
@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


# =========================
# LAB TEST ADMIN
# =========================
@admin.register(LabTest)
class LabTestAdmin(admin.ModelAdmin):
    list_display = ("id", "lab", "get_name", "price", "is_active")
    list_editable = ("price", "is_active")
    search_fields = ("lab__lab_name", "custom_name", "test__name")


# =========================
# LAB REPORT ADMIN
# =========================
@admin.register(LabReport)
class LabReportAdmin(admin.ModelAdmin):
    list_display = ("id", "appointment", "uploaded_at")
    search_fields = ("appointment__full_name",)


# =========================
# LAB WORKING HOURS
# =========================
@admin.register(LabWorkingHours)
class LabWorkingHoursAdmin(admin.ModelAdmin):
    list_display = ("lab", "day", "start_time", "end_time", "is_closed")
    list_editable = ("is_closed",)


# =========================
# LAB AVAILABILITY
# =========================
@admin.register(LabAvailability)
class LabAvailabilityAdmin(admin.ModelAdmin):
    list_display = ("lab", "is_available", "start_time", "end_time")
    list_editable = ("is_available",)


# =========================
# INLINE: PAYMENT
# =========================
class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ("transaction_id", "created_at")


# =========================
# INLINE: PRESCRIPTION
# =========================
class PrescriptionInline(admin.TabularInline):
    model = Prescription
    extra = 1


# =========================
# ACTIONS
# =========================
def approve(modeladmin, request, queryset):
    for obj in queryset:
        obj.status = "Approved"
        obj.approved_at = timezone.now()
        obj.save()

def complete(modeladmin, request, queryset):
    for obj in queryset:
        obj.status = "Completed"
        obj.completed_at = timezone.now()
        obj.save()

def cancel(modeladmin, request, queryset):
    queryset.update(status="Cancelled")


# =========================
# APPOINTMENT ADMIN
# =========================
@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "id", "full_name", "doctor",
        "appointment_date", "status", "is_paid"
    )

    list_filter = ("status", "appointment_date")
    search_fields = ("full_name", "email")

    list_editable = ("status", "is_paid")

    readonly_fields = ("booking_id", "created_at", "approved_at", "completed_at")

    inlines = [PaymentInline, PrescriptionInline]

    actions = [approve, complete, cancel]


# =========================
# PAYMENT ADMIN
# =========================
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "appointment", "amount", "status")
    list_filter = ("status",)
    search_fields = ("transaction_id", "user__email")


# =========================
# LAB APPOINTMENT ADMIN
# =========================
@admin.register(LabAppointment)
class LabAppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "id", "full_name", "lab",
        "appointment_date", "status", "is_paid"
    )

    list_filter = ("status", "appointment_date")
    search_fields = ("full_name", "email")

    list_editable = ("status", "is_paid")

    readonly_fields = ("booking_id", "created_at", "approved_at", "completed_at")

    actions = [approve, complete, cancel]
    
    
