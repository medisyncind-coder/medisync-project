from django import forms
from django.forms import modelformset_factory
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Doctor, Lab, LabTest, Test, Patient
from appointments.models import Appointment

User = get_user_model()


# ======================================================
# 👨‍⚕️ Doctor Registration Form
# ======================================================

class DoctorRegistrationForm(forms.ModelForm):

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    available_days = forms.MultipleChoiceField(
        choices=Doctor.AVAILABLE_DAYS,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time','class':'form-control'}),
        required=False
    )

    end_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time','class':'form-control'}),
        required=False
    )

    class Meta:
        model = Doctor
        exclude = ['user']

    # Email validation
    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("This email is already registered.")
        return email

    # Password validation
    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password:

            if password != confirm_password:
                self.add_error("confirm_password","Passwords do not match")

            if len(password) < 6:
                self.add_error("password","Password must be at least 6 characters")

        return cleaned_data


# ======================================================
# 🏥 Lab Registration Form
# ======================================================

class LabRegistrationForm(forms.ModelForm):

    # ============================================
    # ACCOUNT FIELDS
    # ============================================

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "Official Email"
        })
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Create Password"
        })
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Confirm Password"
        })
    )

    # ============================================
    # OPERATING DAYS (PROFESSIONAL VERSION)
    # ============================================

    OPERATING_DAYS = [
        ("Monday", "Monday"),
        ("Tuesday", "Tuesday"),
        ("Wednesday", "Wednesday"),
        ("Thursday", "Thursday"),
        ("Friday", "Friday"),
        ("Saturday", "Saturday"),
        ("Sunday", "Sunday"),
    ]

    operating_days = forms.MultipleChoiceField(
        choices=OPERATING_DAYS,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    # ============================================
    # TEST SELECTION
    # ============================================

    available_tests = forms.ModelMultipleChoiceField(
        queryset=Test.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:

        model = Lab

        exclude = [
            "user",
            "otp",
            "otp_created_at",
            "is_verified",
            "created_at",
            "updated_at"
        ]

        widgets = {

            "lab_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter Lab Name"
            }),

            "owner_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Owner Name"
            }),

            "registration_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Registration Number"
            }),

            "contact_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Contact Number"
            }),

            "emergency_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Emergency Number"
            }),

            "address": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3
            }),

            "city": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "state": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "pincode": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "6 digit pincode"
            }),

            "lab_type": forms.Select(attrs={
                "class": "form-control"
            }),

            "opening_time": forms.TimeInput(attrs={
                "class": "form-control",
                "type": "time"
            }),

            "closing_time": forms.TimeInput(attrs={
                "class": "form-control",
                "type": "time"
            }),

            "average_report_time": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Example: 24 hours"
            }),
        }

    # ============================================
    # EMAIL VALIDATION
    # ============================================

    def clean_email(self):

        email = self.cleaned_data.get("email")

        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("This email is already registered.")

        return email


    # ============================================
    # PASSWORD VALIDATION
    # ============================================

    def clean(self):

        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password:

            if password != confirm_password:
                self.add_error(
                    "confirm_password",
                    "Passwords do not match."
                )

            if len(password) < 6:
                self.add_error(
                    "password",
                    "Password must be at least 6 characters."
                )

        return cleaned_data


    # ============================================
    # CONTACT NUMBER VALIDATION
    # ============================================

    def clean_contact_number(self):

        number = self.cleaned_data.get("contact_number")

        if not number.isdigit():
            raise ValidationError("Contact number must contain digits only.")

        if len(number) < 10 or len(number) > 15:
            raise ValidationError("Enter valid contact number (10-15 digits).")

        return number


    # ============================================
    # PINCODE VALIDATION
    # ============================================

    def clean_pincode(self):

        pincode = self.cleaned_data.get("pincode")

        if not pincode.isdigit() or len(pincode) != 6:
            raise ValidationError("Enter valid 6-digit pincode.")

        return pincode

# ======================================================
# 🧪 LAB TEST FORM (Lab selects test + price)
# ======================================================

class LabTestForm(forms.ModelForm):

    class Meta:

        model = LabTest

        fields = ["test", "price"]

        widgets = {

            "test": forms.Select(attrs={
                "class": "form-control"
            }),

            "price": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter Price",
                "min": "0"
            })
        }

    def clean_price(self):

        price = self.cleaned_data.get("price")

        if price is None:
            raise ValidationError("Price is required.")

        if price <= 0:
            raise ValidationError("Price must be greater than 0.")

        return price


# ======================================================
# 🧪 MULTIPLE LAB TEST FORMSET
# ======================================================

LabTestFormSet = modelformset_factory(
    LabTest,
    form=LabTestForm,
    extra=1,
    can_delete=True
)


# ======================================================
# 🔐 OTP VERIFICATION FORM
# ======================================================

class OTPVerificationForm(forms.Form):

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "Registered Email"
        })
    )

    otp = forms.CharField(
        max_length=6,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter 6 digit OTP"
        })
    )

    def clean_otp(self):

        otp = self.cleaned_data.get("otp")

        if not otp.isdigit():
            raise ValidationError("OTP must contain digits only.")

        if len(otp) != 6:
            raise ValidationError("OTP must be 6 digits.")

        return otp
    
# ======================================================
# 👨‍⚕️ Patient Registration Form
# ======================================================
class PatientRegistrationForm(forms.ModelForm):

    # =========================
    # ACCOUNT FIELDS
    # =========================

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "Enter Email"
        })
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Create Password"
        })
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Confirm Password"
        })
    )

    # =========================
    # GENDER
    # =========================

    GENDER_CHOICES = [
        ("Male", "Male"),
        ("Female", "Female"),
        ("Other", "Other"),
    ]

    gender = forms.ChoiceField(
        choices=GENDER_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"})
    )

    # =========================
    # META
    # =========================

    class Meta:
        model = Patient

        exclude = ["user"]

        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(attrs={"class": "form-control"}),
            "date_of_birth": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "blood_group": forms.TextInput(attrs={"class": "form-control"}),
            "allergies": forms.Textarea(attrs={"class": "form-control"}),
            "medical_conditions": forms.Textarea(attrs={"class": "form-control"}),
            "emergency_contact": forms.TextInput(attrs={"class": "form-control"}),
            "profile_photo": forms.FileInput(attrs={"class": "form-control"}),
            "pincode": forms.TextInput(attrs={"class": "form-control"}),
            "full_address": forms.Textarea(attrs={"class": "form-control"}),
        }

    # =========================
    # EMAIL VALIDATION
    # =========================

    def clean_email(self):
        email = self.cleaned_data.get("email")

        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Email already registered.")

        return email

    # =========================
    # PASSWORD VALIDATION
    # =========================

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password:
            if password != confirm_password:
                self.add_error("confirm_password", "Passwords do not match.")

            if len(password) < 6:
                self.add_error("password", "Password must be at least 6 characters.")

        return cleaned_data

    # =========================
    # PHONE VALIDATION
    # =========================

    def clean_phone(self):
        phone = self.cleaned_data.get("phone")

        if not phone.isdigit():
            raise ValidationError("Phone must contain digits only.")

        if len(phone) != 10:
            raise ValidationError("Enter valid 10-digit phone number.")

        return phone

    # =========================
    # PINCODE VALIDATION
    # =========================

    def clean_pincode(self):
        pincode = self.cleaned_data.get("pincode")

        if pincode and (not pincode.isdigit() or len(pincode) != 6):
            raise ValidationError("Enter valid 6-digit pincode.")

        return pincode

    # =========================
    # SAVE (NO PASSWORD HERE ❗)
    # =========================

    def save(self, commit=True):
        patient = super().save(commit=False)

        if commit:
            patient.save()

        return patient