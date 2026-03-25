from django.db import models
from django.utils import timezone
from accounts.models import User
#from Doctor.models import Doctor
import uuid
from django.conf import settings

# Create your models here.
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
    # RELATION
    # =========================
    doctor = models.ForeignKey("Doctor.Doctor", on_delete=models.CASCADE)
    patient = models.ForeignKey(User, on_delete=models.CASCADE)

    # =========================
    # APPOINTMENT INFO
    # =========================
    #preferred_date = models.DateField()
    #preferred_time = models.TimeField()
    consultation_mode = models.CharField(max_length=20, choices=CONSULT_MODE)
    payment_type = models.CharField(max_length=50, default="Online")
    is_paid = models.BooleanField(default=False)
    appointment_date = models.DateField()
    appointment_time = models.TimeField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )

    booking_id = models.CharField(max_length=20, unique=True, blank=True)

    # =========================
    # EXTRA FIELDS
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

    # =========================
    # AUTO BOOKING ID GENERATE
    # =========================
    def save(self, *args, **kwargs):
        if not self.booking_id:
            self.booking_id = str(uuid.uuid4())[:10].upper()
        super().save(*args, **kwargs)

    # =========================
    # STATUS METHODS
    # =========================
    def mark_approved(self):
        self.status = 'Approved'
        self.approved_at = timezone.now()
        self.save()

    def mark_completed(self):
        self.status = 'Completed'
        self.completed_at = timezone.now()
        self.save()

    def __str__(self):
        doctor_name = self.doctor.name if self.doctor else "No Doctor"
        return f"{self.full_name} - {doctor_name} ({self.status})"
    
class Payment(models.Model):
    PAYMENT_STATUS = (
        ('Pending', 'Pending'),
        ('Success', 'Success'),
        ('Failed', 'Failed'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    appointment = models.OneToOneField('Appointment', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    payment_method = models.CharField(max_length=20)
    status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default='Pending')
    transaction_id = models.CharField(max_length=100, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = str(uuid.uuid4()).replace('-', '')[:12].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.transaction_id

class Prescription(models.Model):

    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name="prescriptions"  # 🔥 IMPORTANT
    )

    medicine = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100)
    instructions = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

class LabAppointment(models.Model):

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

    SAMPLE_TYPE = [
        ('Lab Visit', 'Lab Visit'),
        ('Home Collection', 'Home Collection'),
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
    # TEST INFO
    # =========================
    test_name = models.CharField(max_length=200)
    notes = models.TextField(blank=True, null=True)
    test_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    # =========================
    # RELATION
    # =========================
    lab = models.ForeignKey(
        "Doctor.Lab",
        on_delete=models.CASCADE,
        related_name="appointments"
    )

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lab_tests"
    )

    # =========================
    # APPOINTMENT INFO
    # =========================
    sample_collection = models.CharField(
        max_length=20,
        choices=SAMPLE_TYPE,
        default="Lab Visit"
    )

    payment_type = models.CharField(max_length=50, default="Online")

    is_paid = models.BooleanField(default=False)

    appointment_date = models.DateField()

    appointment_time = models.TimeField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )

    booking_id = models.CharField(max_length=20, unique=True, blank=True)

    # =========================
    # REPORT SYSTEM
    # =========================
    report_file = models.FileField(
        upload_to='lab_reports/',
        blank=True,
        null=True
    )

    approved_at = models.DateTimeField(blank=True, null=True)

    completed_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    # =========================
    # AUTO BOOKING ID
    # =========================
    def save(self, *args, **kwargs):

        if not self.booking_id:
            self.booking_id = str(uuid.uuid4())[:10].upper()

        super().save(*args, **kwargs)

    # =========================
    # STATUS METHODS
    # =========================
    def mark_approved(self):

        self.status = 'Approved'
        self.approved_at = timezone.now()
        self.save()

    def mark_completed(self):

        self.status = 'Completed'
        self.completed_at = timezone.now()
        self.save()

    def __str__(self):

        lab_name = self.lab.lab_name if self.lab else "No Lab"

        return f"{self.full_name} - {lab_name} ({self.status})"