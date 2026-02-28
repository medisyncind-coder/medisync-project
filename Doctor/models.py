from django.db import models
from django.conf import settings
import random
from django.core.mail import send_mail
from django.utils import timezone
from django.core.validators import RegexValidator, MinValueValidator
from decimal import Decimal

from accounts.models import User


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
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    day = models.CharField(max_length=10)
    is_available = models.BooleanField(default=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    reason = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.doctor.name} - {self.day}"


# =====================================================
# 📅 Appointment Model
# =====================================================

class Appointment(models.Model):

    # =========================
    # STATUS SYSTEM
    # =========================
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    CONSULT_MODE = [
        ('Online', 'Online'),
        ('In-person', 'In-person'),
    ]

    # =========================
    # PATIENT INFO
    # =========================
    full_name = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    contact_number = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField(blank=True, null=True)

    # =========================
    # MEDICAL INFO
    # =========================
    symptoms = models.TextField()
    existing_diseases = models.TextField(blank=True, null=True)
    current_medications = models.TextField(blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)

    # =========================
    # DOCTOR INFO
    # =========================
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    patient = models.ForeignKey(User, on_delete=models.CASCADE)

    # =========================
    # APPOINTMENT INFO
    # =========================
    preferred_date = models.DateField()
    preferred_time = models.TimeField()
    consultation_mode = models.CharField(max_length=20, choices=CONSULT_MODE)
    payment_type = models.CharField(max_length=50, default="Online")

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )

    booking_id = models.CharField(max_length=20, unique=True)

    # =========================
    # EXTRA PROFESSIONAL FIELDS
    # =========================
    cancellation_reason = models.TextField(blank=True, null=True)
    prescription_file = models.FileField(
        upload_to='prescriptions/',
        blank=True,
        null=True
    )

    approved_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def mark_approved(self):
        self.status = 'Approved'
        self.approved_at = timezone.now()
        self.save()

    def mark_completed(self):
        self.status = 'Completed'
        self.completed_at = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.full_name} - {self.doctor_name} ({self.status})"

# =====================================================
# 🧪 Test Model
# =====================================================
class Test(models.Model):

    name = models.CharField(
        max_length=100,
        unique=True,
        db_index=True
    )

    description = models.TextField(blank=True, null=True)

    default_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    test_image = models.ImageField(
        upload_to='test_images/',
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Medical Test"
        verbose_name_plural = "Medical Tests"

    def __str__(self):
        return f"{self.name} (₹{self.default_price})"


# =====================================================
# 🏥 LAB MODEL (OTP handled here)
# =====================================================

class Lab(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name="labs")

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
        ('Pathology', 'Pathology'),
        ('Radiology', 'Radiology'),
        ('Diagnostic Center', 'Diagnostic Center'),
        ('Multi-specialty', 'Multi-specialty'),
    ]

    lab_type = models.CharField(
        max_length=50,
        choices=LAB_TYPE_CHOICES,
        default='Pathology',
        db_index=True
    )

    home_sample_collection = models.BooleanField(default=False)

    operating_days = models.CharField(max_length=100)
    opening_time = models.TimeField()
    closing_time = models.TimeField()

    average_report_time = models.CharField(max_length=50)

    # 🔐 OTP SYSTEM
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)

    is_verified = models.BooleanField(default=False)

    # Auto Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Diagnostic Lab"
        verbose_name_plural = "Diagnostic Labs"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['city']),
            models.Index(fields=['lab_type']),
            models.Index(fields=['is_verified']),
        ]

    def __str__(self):
        return f"{self.lab_name} ({self.city})"

    # =====================================================
    # 🔢 OTP GENERATE
    # =====================================================
    def generate_otp(self):
        otp = str(random.randint(100000, 999999))
        self.otp = otp
        self.otp_created_at = timezone.now()
        self.save()
        return otp

    # =====================================================
    # 🔒 OTP VERIFY (5 min expiry)
    # =====================================================
    def verify_otp(self, entered_otp):
        if not self.otp or not self.otp_created_at:
            return False

        # OTP Expiry 5 Minutes
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
# 💰 LAB TEST MAPPING
# =====================================================

class LabTest(models.Model):

    lab = models.ForeignKey(
        Lab,
        on_delete=models.CASCADE,
        related_name="lab_tests"
    )

    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        related_name="available_in_labs"
    )

    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    test_image = models.ImageField(
        upload_to='lab_test_images/',
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('lab', 'test')
        verbose_name = "Lab Test"
        verbose_name_plural = "Lab Tests"
        ordering = ['test__name']
        indexes = [
            models.Index(fields=['lab']),
            models.Index(fields=['test']),
        ]

    def __str__(self):
        return f"{self.test.name} - ₹{self.price} ({self.lab.lab_name})"
    
# =====================================================
# 🧾 LAB APPOINTMENT (User Books Test)
# =====================================================

class LabAppointment(models.Model):

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="lab_appointments"
    )

    lab = models.ForeignKey(
        Lab,
        on_delete=models.CASCADE,
        related_name="appointments"
    )

    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE
    )

    appointment_date = models.DateField()
    appointment_time = models.TimeField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.test.name} ({self.status})"
    
    
# =====================================================
# 📁 LAB REPORT UPLOAD
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
        return f"Report - {self.appointment.user.email}"