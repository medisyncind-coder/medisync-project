from django.db import models
from django.conf import settings
import random
from django.core.mail import send_mail
from django.utils import timezone
from django.core.validators import RegexValidator, MinValueValidator
from decimal import Decimal
from accounts.models import User
from appointments.models import *
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator


# =====================================================
# 👨‍⚕️ Doctor Model (FIXED & REGISTRATION FRIENDLY)
# =====================================================
class Doctor(models.Model):
    user = models.OneToOneField(
    User,
    on_delete=models.CASCADE,
    null=True,
    blank=True
)

    # -------- BASIC INFO --------
    name = models.CharField(max_length=100)
    qualification = models.CharField(max_length=200)
    specialization = models.CharField(max_length=100)
    registration_number = models.CharField(max_length=50, unique=True)
    experience = models.IntegerField(help_text="Years of experience")
    contact_number = models.CharField(max_length=15)
    address = models.TextField()

    # -------- CLINIC INFO --------
    clinic_name = models.CharField(max_length=150, blank=True, null=True)

    consultation_fee = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True
    )
    
    AVAILABLE_DAYS = [
    ('Mon', 'Monday'),
    ('Tue', 'Tuesday'),
    ('Wed', 'Wednesday'),
    ('Thu', 'Thursday'),
    ('Fri', 'Friday'),
    ('Sat', 'Saturday'),
    ('Sun', 'Sunday'),
]
    available_days = models.JSONField(blank=True, null=True)
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)


   

    appointment_duration = models.IntegerField(
        default=15,
        blank=True,
        null=True
    )

    # -------- CONSULTATION --------
    CONSULTATION_CHOICES = [
        ('Online', 'Online'),
        ('Offline', 'Offline'),
        ('Both', 'Both'),
    ]

    consultation_type = models.CharField(
        max_length=20,
        choices=CONSULTATION_CHOICES,
        default='Offline',
        blank=True,
        null=True
    )

    online_consultation_time = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    mode_of_appointment = models.CharField(
        max_length=50,
        choices=[('In-person', 'In-person'), ('Online', 'Online')],
        default='In-person',
        blank=True,
        null=True
    )

    # -------- EDUCATION & LOCATION --------
    education_institution = models.CharField(max_length=200, blank=True, null=True)

    full_address = models.TextField(blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    emergency_number = models.CharField(max_length=15, blank=True, null=True)

    # -------- FILES --------
    degree_certificate = models.ImageField(
        upload_to='doctor_degrees/',
        blank=True,
        null=True
    )

    photo_1 = models.ImageField(upload_to='hospital_photos/', blank=True, null=True)
    photo_2 = models.ImageField(upload_to='hospital_photos/', blank=True, null=True)
    photo_3 = models.ImageField(upload_to='hospital_photos/', blank=True, null=True)
    photo_4 = models.ImageField(upload_to='hospital_photos/', blank=True, null=True)
    photo_5 = models.ImageField(upload_to='hospital_photos/', blank=True, null=True)
    photo_6 = models.ImageField(upload_to='hospital_photos/', blank=True, null=True)
    photo_7 = models.ImageField(upload_to='hospital_photos/', blank=True, null=True)

    profile_photo = models.ImageField(
        upload_to='doctor_photos/',
        blank=True,
        null=True
    )

    bio = models.TextField(blank=True, null=True)
    location_link = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name


# =====================================================
# ⏰ Doctor Availability
# =====================================================
class DoctorAvailability(models.Model):

    doctor = models.OneToOneField(
        Doctor,
        on_delete=models.CASCADE
    )

    is_available = models.BooleanField(default=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        status = "Available" if self.is_available else "Unavailable"
        return f"{self.doctor.name} - {status}"



# =====================================================
# 🧪 Test Model
# =====================================================
class Test(models.Model):

    name = models.CharField(
        max_length=100,
        unique=True,
        db_index=True
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    test_image = models.ImageField(
        upload_to="test_images/",
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Medical Test"
        verbose_name_plural = "Medical Tests"

    def __str__(self):
        return self.name


# =====================================================
# 🏥 LAB MODEL (OTP SYSTEM INCLUDED)
# =====================================================

class Lab(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="labs"
    )

    phone_validator = RegexValidator(
        regex=r'^\d{10,15}$',
        message="Enter valid contact number (10-15 digits)."
    )

    pincode_validator = RegexValidator(
        regex=r'^\d{6}$',
        message="Enter valid 6-digit pincode."
    )

    lab_name = models.CharField(max_length=150, db_index=True)

    owner_name = models.CharField(max_length=100)

    registration_number = models.CharField(
        max_length=50,
        unique=True
    )

    contact_number = models.CharField(
        max_length=15,
        validators=[phone_validator]
    )

    emergency_number = models.CharField(
        max_length=15,
        validators=[phone_validator],
        blank=True,
        null=True
    )

    email = models.EmailField(unique=True, db_index=True)

    address = models.TextField()

    city = models.CharField(max_length=100, db_index=True)

    state = models.CharField(max_length=100)

    pincode = models.CharField(
        max_length=6,
        validators=[pincode_validator]
    )

    LAB_TYPE_CHOICES = [
        ("Pathology", "Pathology"),
        ("Radiology", "Radiology"),
        ("Diagnostic Center", "Diagnostic Center"),
        ("Multi-specialty", "Multi-specialty"),
    ]

    lab_type = models.CharField(
        max_length=50,
        choices=LAB_TYPE_CHOICES,
        default="Pathology",
        db_index=True
    )

    home_sample_collection = models.BooleanField(default=False)

    operating_days = models.CharField(max_length=100)

    opening_time = models.TimeField()

    closing_time = models.TimeField()

    average_report_time = models.CharField(max_length=50)

    otp = models.CharField(max_length=6, blank=True, null=True)

    otp_created_at = models.DateTimeField(blank=True, null=True)

    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:

        verbose_name = "Diagnostic Lab"
        verbose_name_plural = "Diagnostic Labs"
        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["city"]),
            models.Index(fields=["lab_type"]),
            models.Index(fields=["is_verified"]),
        ]

    def __str__(self):
        return f"{self.lab_name} ({self.city})"

    def total_tests(self):
        return self.tests.count()


    # =====================================================
    # OTP GENERATION
    # =====================================================

    def generate_otp(self):

        otp = str(random.randint(100000, 999999))

        self.otp = otp
        self.otp_created_at = timezone.now()

        self.save()

        return otp


    # =====================================================
    # OTP VERIFICATION
    # =====================================================

    def verify_otp(self, entered_otp):

        if not self.otp or not self.otp_created_at:
            return False

        expiry_time = self.otp_created_at + timezone.timedelta(minutes=5)

        if timezone.now() > expiry_time:
            return False

        if self.otp == entered_otp:

            self.otp = None
            self.is_verified = True
            self.save()

            return True

        return False


# =====================================================
# 💰 LAB TEST MAPPING (Lab + Test + Price)
# =====================================================

class LabTest(models.Model):

    lab = models.ForeignKey(
        Lab,
        on_delete=models.CASCADE,
        related_name="tests"
    )

    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        related_name="lab_tests",
        null=True,
        blank=True
    )

    price = models.DecimalField(
        max_digits=8,
        decimal_places=2
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    custom_name = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ("lab", "test")
        ordering = ["id"]

    # 🔥 IMPORTANT FIX
    def get_name(self):
        if self.custom_name:
            return self.custom_name
        elif self.test:
            return self.test.name
        return "Test Not Available"

    def __str__(self):
        return f"{self.lab.lab_name} - {self.get_name()} (₹{self.price})"
# =====================================================
# 📅 LAB APPOINTMENT SYSTEM
# =====================================================


# =====================================================
# 📁 LAB REPORT SYSTEM
# =====================================================

class LabReport(models.Model):

    appointment = models.OneToOneField(
        LabAppointment,
        on_delete=models.CASCADE,
        related_name="report"
    )

    report_file = models.FileField(upload_to="lab_reports/")

    remarks = models.TextField(blank=True, null=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report - {self.appointment.patient}"


# =====================================================
# ⏰ LAB WORKING HOURS
# =====================================================

class LabWorkingHours(models.Model):

    lab = models.ForeignKey(
        Lab,
        on_delete=models.CASCADE,
        related_name="working_hours"
    )

    day = models.CharField(max_length=20)

    start_time = models.TimeField()

    end_time = models.TimeField()

    is_closed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.lab.lab_name} - {self.day}"


# =====================================================
# 🔘 LAB AVAILABILITY
# =====================================================

class LabAvailability(models.Model):

    lab = models.OneToOneField(
        Lab,
        on_delete=models.CASCADE,
        related_name="availability"
    )

    is_available = models.BooleanField(default=True)

    start_time = models.TimeField(blank=True, null=True)

    end_time = models.TimeField(blank=True, null=True)

    break_start = models.TimeField(blank=True, null=True)

    break_end = models.TimeField(blank=True, null=True)

    monday = models.BooleanField(default=True)
    tuesday = models.BooleanField(default=True)
    wednesday = models.BooleanField(default=True)
    thursday = models.BooleanField(default=True)
    friday = models.BooleanField(default=True)
    saturday = models.BooleanField(default=True)
    sunday = models.BooleanField(default=False)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):

        status = "Open" if self.is_available else "Closed"

        return f"{self.lab.lab_name} - {status}"
    
    
# =====================================================
#  User Model (for Lab and Doctor registration)
# =====================================================
    
    


User = get_user_model()   # ✅ BEST PRACTICE (custom user safe)


class Patient(models.Model):

    # 🔗 LINK WITH USER
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="patient_profile")

    # -------- VALIDATORS --------
    phone_validator = RegexValidator(
        regex=r'^\d{10}$',
        message="Enter a valid 10-digit phone number"
    )

    pincode_validator = RegexValidator(
        regex=r'^\d{6}$',
        message="Enter a valid 6-digit pincode"
    )

    # -------- REQUIRED FIELDS --------
    name = models.CharField(max_length=100)

    phone = models.CharField(
        max_length=10,
        validators=[phone_validator]
    )

    address = models.TextField()

    date_of_birth = models.DateField(null=True, blank=True)

    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)

    # -------- OPTIONAL FIELDS --------
    blood_group = models.CharField(max_length=5, blank=True, null=True)

    allergies = models.TextField(blank=True, null=True)
    medical_conditions = models.TextField(blank=True, null=True)

    emergency_contact = models.CharField(
        max_length=10,
        validators=[phone_validator],
        blank=True,
        null=True
    )

    profile_photo = models.ImageField(
        upload_to='patient_photos/',
        blank=True,
        null=True
    )

    pincode = models.CharField(
        max_length=6,
        validators=[pincode_validator],
        blank=True,
        null=True
    )

    full_address = models.TextField(blank=True, null=True)

    # -------- STRING --------
    def __str__(self):
        return f"{self.name} ({self.user.email})"
        return self.name
    
    
class MedicalRecord(models.Model):
    patient = models.ForeignKey(User, on_delete=models.CASCADE)  # 🔥 CHANGE
    file = models.FileField(upload_to="records/")
    uploaded_at = models.DateTimeField(auto_now_add=True)