from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from accounts.models import User



# =========================
# IMPORT MODELS
# =========================

from Doctor.models import (
    Patient,
    Doctor,
    Lab,
    MedicalRecord,
    DoctorAvailability,
    LabWorkingHours,
    LabAvailability,
    LabReport,
    LabTest,
    Test
)

from appointments.models import (
    Appointment,
    Payment,
    Prescription,
    LabAppointment
)
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin




# =========================
# 🔥 GLOBAL PERMISSION MIXIN
# =========================
class FullAccessAdmin(admin.ModelAdmin):

    def has_view_permission(self, request, obj=None):
        return True

    def has_add_permission(self, request):
        return True

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return True


# =========================
# PATIENT ADMIN
# =========================


@admin.register(Patient)
class PatientAdmin(FullAccessAdmin):

    # ===== LIST VIEW =====
    list_display = (
        "id",
        "name",
        "user_email",
        "phone",
        "gender",
        "blood_group",
        "profile_preview"
    )

    search_fields = (
        "name",
        "user__email",
        "phone"
    )

    list_filter = (
        "gender",
        "blood_group"
    )

    ordering = ("-id",)

    # ===== DETAIL PAGE =====
    fieldsets = (

        ("👤 BASIC INFO", {
            "fields": (
                "user",
                "name",
                "phone",
                "gender",
                "date_of_birth"
            )
        }),

        ("🩺 MEDICAL INFO", {
            "fields": (
                "blood_group",
                "allergies",
                "medical_conditions"
            )
        }),

        ("📞 CONTACT INFO", {
            "fields": (
                "emergency_contact",
                "address",
                "pincode",
                "full_address"
            )
        }),

        ("🖼️ PROFILE", {
            "fields": (
                "profile_photo",
                "photo_preview"
            )
        }),
    )

    readonly_fields = ("photo_preview",)

    # ===== USER EMAIL DISPLAY =====
    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = "Email"

    # ===== IMAGE PREVIEW (DETAIL PAGE) =====
    def photo_preview(self, obj):
        if obj.profile_photo:
            return format_html(
                '<img src="{}" style="height:100px; border-radius:10px;" />',
                obj.profile_photo.url
            )
        return "No Image"

    photo_preview.short_description = "Preview"

    # ===== IMAGE PREVIEW (LIST VIEW) =====
    def profile_preview(self, obj):
        if obj.profile_photo:
            return format_html(
                '<img src="{}" style="height:40px; width:40px; border-radius:50%;" />',
                obj.profile_photo.url
            )
        return "-"

    profile_preview.short_description = "Photo"


# =========================
# DOCTOR ADMIN
# =========================
@admin.register(Doctor)
class DoctorAdmin(FullAccessAdmin):

    # ===== LIST VIEW (TABLE) =====
    list_display = (
        "id",
        "name",
        "specialization",
        "experience",
        "consultation_fee",
        "consultation_type",
        "mode_of_appointment"
    )

    search_fields = ("name", "specialization", "registration_number")
    list_filter = ("consultation_type", "mode_of_appointment", "experience")

    # ===== DETAIL PAGE (FULL INFO) =====
    fieldsets = (

        ("👤 BASIC INFO", {
            "fields": (
                "user",
                "name",
                "qualification",
                "specialization",
                "registration_number",
                "experience",
                "contact_number",
                "address"
            )
        }),

        ("🏥 CLINIC INFO", {
            "fields": (
                "clinic_name",
                "consultation_fee",
                "available_days",
                "start_time",
                "end_time",
                "appointment_duration"
            )
        }),

        ("💻 CONSULTATION", {
            "fields": (
                "consultation_type",
                "online_consultation_time",
                "mode_of_appointment"
            )
        }),

        ("🎓 EDUCATION & LOCATION", {
            "fields": (
                "education_institution",
                "full_address",
                "pincode",
                "emergency_number",
                "location_link"
            )
        }),

        ("📄 DOCUMENTS", {
            "fields": (
                "degree_certificate",
                "profile_photo"
            )
        }),

        ("🖼️ HOSPITAL PHOTOS", {
            "fields": (
                "photo_1",
                "photo_2",
                "photo_3",
                "photo_4",
                "photo_5",
                "photo_6",
                "photo_7"
            )
        }),

        ("📝 EXTRA", {
            "fields": (
                "bio",
            )
        }),
    )

    # ===== OPTIONAL =====
    readonly_fields = ()  # sab editable

    # ===== BETTER UI =====
    list_per_page = 20


# =========================
# LAB ADMIN
# =========================
@admin.register(Lab)
class LabAdmin(FullAccessAdmin):

    # ===== LIST VIEW =====
    list_display = (
        "id",
        "lab_name",
        "city",
        "lab_type",
        "is_verified",
        "home_sample_collection",
        "contact_number"
    )

    list_filter = ("city", "lab_type", "is_verified", "home_sample_collection")
    search_fields = ("lab_name", "city", "email", "registration_number")

    ordering = ("-created_at",)

    # ===== DETAIL PAGE =====
    fieldsets = (

        ("🏥 BASIC INFO", {
            "fields": (
                "user",
                "lab_name",
                "owner_name",
                "registration_number"
            )
        }),

        ("📞 CONTACT INFO", {
            "fields": (
                "contact_number",
                "emergency_number",
                "email"
            )
        }),

        ("📍 LOCATION", {
            "fields": (
                "address",
                "city",
                "state",
                "pincode"
            )
        }),

        ("🧪 LAB DETAILS", {
            "fields": (
                "lab_type",
                "home_sample_collection",
                "operating_days",
                "opening_time",
                "closing_time",
                "average_report_time"
            )
        }),

        ("🔐 VERIFICATION", {
            "fields": (
                "is_verified",
                "otp",
                "otp_created_at"
            )
        }),

        ("🕒 SYSTEM INFO", {
            "fields": (
                "created_at",
                "updated_at"
            )
        }),
    )

    readonly_fields = ("otp", "otp_created_at", "created_at", "updated_at")

    actions = ["verify_labs"]

    def verify_labs(self, request, queryset):
        queryset.update(is_verified=True)


# =========================
# MEDICAL RECORD
# =========================

@admin.register(MedicalRecord)
class MedicalRecordAdmin(FullAccessAdmin):

    # ===== LIST VIEW =====
    list_display = (
        "id",
        "patient_email",
        "file_preview",
        "uploaded_at"
    )

    search_fields = (
        "patient__email",
    )

    list_filter = ("uploaded_at",)

    ordering = ("-uploaded_at",)

    # ===== DETAIL PAGE =====
    fieldsets = (

        ("👤 PATIENT INFO", {
            "fields": (
                "patient",
            )
        }),

        ("📁 RECORD FILE", {
            "fields": (
                "file",          # ✅ FIX
                "preview_file"
            )
        }),

        ("🕒 SYSTEM INFO", {
            "fields": (
                "uploaded_at",
            )
        }),
    )

    readonly_fields = ("uploaded_at", "preview_file")

    # ===== PATIENT EMAIL =====
    def patient_email(self, obj):
        return obj.patient.email

    patient_email.short_description = "Patient Email"

    # ===== FILE PREVIEW =====
    def preview_file(self, obj):
        if obj.file:   # ✅ FIX
            return format_html(
                '<a href="{}" target="_blank">📄 View File</a>',
                obj.file.url
            )
        return "No File"

    preview_file.short_description = "Preview"

    # ===== LIST VIEW FILE LINK =====
    def file_preview(self, obj):
        if obj.file:   # ✅ FIX
            return format_html(
                '<a href="{}" target="_blank">Open</a>',
                obj.file.url
            )
        return "-"

    file_preview.short_description = "File"

# =========================
# DOCTOR AVAILABILITY
# =========================
@admin.register(DoctorAvailability)
class DoctorAvailabilityAdmin(FullAccessAdmin):

    # ===== LIST VIEW =====
    list_display = (
        "doctor_name",
        "is_available",
        "updated_at"
    )

    list_editable = ("is_available",)

    list_filter = ("is_available", "updated_at")

    search_fields = (
        "doctor__name",
        "doctor__specialization"
    )

    ordering = ("-updated_at",)

    # ===== DETAIL PAGE =====
    fieldsets = (
        ("👨‍⚕️ DOCTOR INFO", {
            "fields": (
                "doctor",
            )
        }),

        ("⚡ AVAILABILITY STATUS", {
            "fields": (
                "is_available",
            )
        }),

        ("🕒 SYSTEM INFO", {
            "fields": (
                "updated_at",
            )
        }),
    )

    readonly_fields = ("updated_at",)

    # ===== CUSTOM DISPLAY =====
    def doctor_name(self, obj):
        return obj.doctor.name

    doctor_name.short_description = "Doctor Name"


# =========================
# LAB WORKING HOURS
# =========================
@admin.register(LabWorkingHours)
class LabWorkingHoursAdmin(FullAccessAdmin):

    list_display = (
        "lab",
        "day",
        "start_time",
        "end_time",
        "is_closed"
    )

    list_editable = ("is_closed",)

    list_filter = ("day", "is_closed")

    search_fields = ("lab__lab_name",)

    fieldsets = (
        ("⏰ WORKING HOURS", {
            "fields": (
                "lab",
                "day",
                "start_time",
                "end_time",
                "is_closed"
            )
        }),
    )


# =========================
# LAB AVAILABILITY
# =========================
@admin.register(LabAvailability)
class LabAvailabilityAdmin(FullAccessAdmin):

    list_display = (
        "lab",
        "is_available",
        "start_time",
        "end_time",
        "updated_at"
    )

    list_editable = ("is_available",)

    list_filter = ("is_available",)

    search_fields = ("lab__lab_name",)

    fieldsets = (

        ("🏥 LAB", {
            "fields": ("lab",)
        }),

        ("⏰ TIMINGS", {
            "fields": (
                "start_time",
                "end_time",
                "break_start",
                "break_end"
            )
        }),

        ("📅 DAYS", {
            "fields": (
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
                "sunday"
            )
        }),

        ("⚡ STATUS", {
            "fields": ("is_available",)
        }),

        ("🕒 SYSTEM", {
            "fields": ("updated_at",)
        }),
    )

    readonly_fields = ("updated_at",)

# =========================
# TEST ADMIN
# =========================
@admin.register(Test)
class TestAdmin(FullAccessAdmin):

    list_display = ("id", "name", "created_at")
    search_fields = ("name",)

    fieldsets = (
        ("🧪 TEST INFO", {
            "fields": ("name", "description", "test_image")
        }),
        ("🕒 SYSTEM", {
            "fields": ("created_at",)
        }),
    )

    readonly_fields = ("created_at",)


# =========================
# LAB TEST ADMIN
# =========================
@admin.register(LabTest)
class LabTestAdmin(FullAccessAdmin):

    list_display = (
        "id",
        "lab",
        "get_test_name",
        "price",
        "is_active"
    )

    list_editable = ("price", "is_active")

    search_fields = (
        "lab__lab_name",
        "test__name",
        "custom_name"
    )

    list_filter = ("is_active",)

    fieldsets = (
        ("🧪 TEST INFO", {
            "fields": (
                "lab",
                "test",
                "custom_name",
                "description"
            )
        }),

        ("💰 PRICING", {
            "fields": (
                "price",
                "is_active"
            )
        }),

        ("🕒 SYSTEM", {
            "fields": (
                "created_at",
                "updated_at"
            )
        }),
    )

    readonly_fields = ("created_at", "updated_at")

    def get_test_name(self, obj):
        return obj.get_name()

    get_test_name.short_description = "Test Name"


# =========================
# LAB REPORT ADMIN
# =========================
@admin.register(LabReport)
class LabReportAdmin(FullAccessAdmin):

    list_display = (
        "id",
        "appointment",
        "uploaded_at"
    )

    search_fields = ("appointment__patient__name",)

    fieldsets = (
        ("📁 REPORT INFO", {
            "fields": (
                "appointment",
                "report_file",
                "remarks"
            )
        }),

        ("🕒 SYSTEM", {
            "fields": ("uploaded_at",)
        }),
    )

    readonly_fields = ("uploaded_at",)


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
    extra = 0

    # ❌ REMOVE fields completely (best)
    
    readonly_fields = ("created_at",)

    show_change_link = True

# =========================
# ACTIONS
# =========================
def approve(modeladmin, request, queryset):
    queryset.update(status="Approved", approved_at=timezone.now())


def complete(modeladmin, request, queryset):
    queryset.update(status="Completed", completed_at=timezone.now())


def cancel(modeladmin, request, queryset):
    queryset.update(status="Cancelled")


# =========================
# APPOINTMENT ADMIN
# =========================
@admin.register(Appointment)
class AppointmentAdmin(FullAccessAdmin):

    list_display = (
        "id",
        "full_name",
        "doctor",
        "appointment_date",
        "status_badge",
        "is_paid"
    )

    list_filter = ("status", "appointment_date", "is_paid")

    search_fields = ("full_name", "email", "doctor__name")

    list_editable = ("is_paid",)

    ordering = ("-appointment_date",)

    readonly_fields = (
        "booking_id",
        "created_at",
        "approved_at",
        "completed_at"
    )

    inlines = [PaymentInline, PrescriptionInline]

    actions = [approve, complete, cancel]

    # 🔥 STATUS COLOR BADGE
    def status_badge(self, obj):
        color = {
            "Pending": "orange",
            "Approved": "blue",
            "Completed": "green",
            "Cancelled": "red",
        }.get(obj.status, "gray")

        return format_html(
            '<b style="color:{};">{}</b>',
            color,
            obj.status
        )

    status_badge.short_description = "Status"


# =========================
# PAYMENT ADMIN
# =========================
@admin.register(Payment)
class PaymentAdmin(FullAccessAdmin):
    list_display = ("id", "user", "appointment", "amount", "status")
    list_filter = ("status",)


# =========================
# LAB APPOINTMENT ADMIN
# =========================
@admin.register(LabAppointment)
class LabAppointmentAdmin(FullAccessAdmin):

    # ===== LIST VIEW =====
    list_display = (
        "id",
        "full_name",
        "lab",
        "appointment_date",
        "status_badge",
        "is_paid",
        "booking_id"
    )

    list_filter = ("status", "appointment_date", "is_paid")

    search_fields = (
        "full_name",
        "email",
        "lab__lab_name"
    )

    list_editable = ("is_paid",)

    ordering = ("-appointment_date",)

    # ===== DETAIL PAGE =====
    fieldsets = (

        ("👤 PATIENT INFO", {
            "fields": (
                "full_name",
                "age",
                "gender",
                "contact_number",
                "email",
                "address",
            )
        }),

        ("🧪 TEST INFO", {
            "fields": (
                "test_name",
                "test_price",
                "notes",
            )
        }),

        ("🏥 LAB INFO", {
            "fields": (
                "lab",
                "patient",
            )
        }),

        ("📅 APPOINTMENT", {
            "fields": (
                "appointment_date",
                "appointment_time",
                "sample_collection",
                "status",
                "is_paid",
            )
        }),

        ("🕒 STATUS TIMELINE", {
            "fields": (
                "created_at",
                "approved_at",
                "completed_at",
            )
        }),

        ("🆔 SYSTEM INFO", {
            "fields": (
                "booking_id",
                "report_file",
            )
        }),
    )

    readonly_fields = (
        "booking_id",
        "created_at",
        "approved_at",
        "completed_at"
    )

    actions = [approve, complete, cancel]

    # 🔥 AUTO TIME SET
    def save_model(self, request, obj, form, change):

        if obj.status == "Approved" and not obj.approved_at:
            obj.approved_at = timezone.now()

        if obj.status == "Completed" and not obj.completed_at:
            obj.completed_at = timezone.now()

        super().save_model(request, obj, form, change)

    # 🔥 STATUS COLOR BADGE
    def status_badge(self, obj):
        color = {
            "Pending": "orange",
            "Approved": "blue",
            "Completed": "green",
            "Cancelled": "red",
        }.get(obj.status, "gray")

        return format_html(
            '<b style="color:{};">{}</b>',
            color,
            obj.status
        )

    status_badge.short_description = "Status"