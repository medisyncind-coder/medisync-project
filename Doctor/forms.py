from django import forms
from django.forms import modelformset_factory
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Doctor, Appointment, Lab, LabTest, Test

User = get_user_model()


# ======================================================
# 👨‍⚕️ Doctor Registration Form
# =====================================================


class DoctorRegistrationForm(forms.ModelForm):

    # ================= AUTH FIELDS =================
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    # ================= AVAILABILITY =================
    available_days = forms.MultipleChoiceField(
        choices=Doctor.AVAILABLE_DAYS,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        required=False
    )

    end_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        required=False
    )

    class Meta:
        model = Doctor
        exclude = ['user']

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'registration_number': forms.TextInput(attrs={'class': 'form-control'}),
            'experience': forms.NumberInput(attrs={'class': 'form-control'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),

            'clinic_name': forms.TextInput(attrs={'class': 'form-control'}),
            'consultation_fee': forms.NumberInput(attrs={'class': 'form-control'}),
            'appointment_duration': forms.NumberInput(attrs={'class': 'form-control'}),

            'consultation_type': forms.Select(attrs={'class': 'form-control'}),
            'online_consultation_time': forms.TextInput(attrs={'class': 'form-control'}),
            'mode_of_appointment': forms.Select(attrs={'class': 'form-control'}),

            'education_institution': forms.TextInput(attrs={'class': 'form-control'}),
            'full_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'pincode': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_number': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'location_link': forms.URLInput(attrs={'class': 'form-control'}),

            'degree_certificate': forms.FileInput(attrs={'class': 'form-control'}),
            'profile_photo': forms.FileInput(attrs={'class': 'form-control'}),
            'photo_1': forms.FileInput(attrs={'class': 'form-control'}),
            'photo_2': forms.FileInput(attrs={'class': 'form-control'}),
            'photo_3': forms.FileInput(attrs={'class': 'form-control'}),
            'photo_4': forms.FileInput(attrs={'class': 'form-control'}),
            'photo_5': forms.FileInput(attrs={'class': 'form-control'}),
            'photo_6': forms.FileInput(attrs={'class': 'form-control'}),
            'photo_7': forms.FileInput(attrs={'class': 'form-control'}),
        }

    # ================= EMAIL UNIQUE =================
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("This email is already registered.")
        return email

    # ================= PASSWORD VALIDATION =================
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password:
            if password != confirm_password:
                self.add_error("confirm_password", "Passwords do not match")

            if len(password) < 6:
                self.add_error("password", "Password must be at least 6 characters long")

        return cleaned_data


# ======================================================
# 📅 Appointment Form
# ======================================================
class AppointmentForm(forms.ModelForm):

    preferred_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )

    preferred_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'form-control'
        })
    )

    class Meta:
        model = Appointment
        exclude = [
            'doctor_name',
            'specialization',
            'booking_id',
            'status',
            'cancellation_reason',
            'prescription_file',
            'approved_at',
            'completed_at',
            'created_at'
        ]

        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'symptoms': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'existing_diseases': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'current_medications': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'allergies': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'consultation_mode': forms.Select(attrs={'class': 'form-control'}),
            'payment_type': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_preferred_date(self):
        date = self.cleaned_data.get('preferred_date')
        if date < timezone.now().date():
            raise ValidationError("You cannot select a past date.")
        return date


# ======================================================
# 🏥 Lab Registration Form
# ======================================================
class LabRegistrationForm(forms.ModelForm):

    # ================= AUTH FIELDS =================
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Official Email Address'
        })
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create Password'
        })
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm Password'
        })
    )

    class Meta:
        model = Lab
        exclude = ['user', 'otp', 'is_verified', 'created_at', 'updated_at']

        widgets = {

            'lab_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Lab Name'
            }),

            'owner_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Owner / Administrator Name'
            }),

            'registration_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Government Registration Number'
            }),

            'contact_number': forms.TextInput(attrs={
                'class': 'form-control',
                'inputmode': 'numeric',
                'placeholder': 'Primary Contact Number'
            }),

            'emergency_number': forms.TextInput(attrs={
                'class': 'form-control',
                'inputmode': 'numeric',
                'placeholder': 'Emergency Contact (Optional)'
            }),

            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),

            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),

            'pincode': forms.TextInput(attrs={
                'class': 'form-control',
                'inputmode': 'numeric',
                'placeholder': '6-digit Pincode'
            }),

            'lab_type': forms.Select(attrs={
                'class': 'form-control'
            }),

            'home_sample_collection': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),

            'operating_days': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Example: Mon-Sat'
            }),

            'opening_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),

            'closing_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),

            'average_report_time': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Example: 24 Hours'
            }),
        }

    # ================= EMAIL UNIQUE =================
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("This email is already registered.")
        return email

    # ================= PASSWORD VALIDATION =================
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password:
            if password != confirm_password:
                self.add_error("confirm_password", "Passwords do not match")

            if len(password) < 6:
                self.add_error("password", "Password must be at least 6 characters long")

        return cleaned_data

    # ================= CONTACT VALIDATION =================
    def clean_contact_number(self):
        number = self.cleaned_data.get('contact_number')
        if not number.isdigit():
            raise ValidationError("Contact number must contain digits only.")
        if len(number) < 10:
            raise ValidationError("Contact number must be at least 10 digits.")
        return number

    def clean_pincode(self):
        pincode = self.cleaned_data.get('pincode')
        if not pincode.isdigit() or len(pincode) != 6:
            raise ValidationError("Enter valid 6-digit pincode.")
        return pincode


# ======================================================
# 🧪 Lab Test Form (Professional Version)
# ======================================================

class LabTestForm(forms.ModelForm):

    test_name = forms.CharField(
        max_length=100,
        label="Test Name",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Test Name'
        })
    )

    class Meta:
        model = LabTest
        fields = ['test_name', 'price', 'test_image']
        widgets = {
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Price',
                'min': '0'
            }),
            'test_image': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
        }

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price <= 0:
            raise ValidationError("Price must be greater than 0.")
        return price

    def save(self, lab=None, commit=True):
        test_name = self.cleaned_data['test_name'].strip()
        price = self.cleaned_data['price']
        test_image = self.cleaned_data.get('test_image')

        test, created = Test.objects.get_or_create(name=test_name)

        if created:
            test.default_price = price
            if test_image:
                test.test_image = test_image
            test.save()

        # Prevent duplicate lab-test entry
        if LabTest.objects.filter(lab=lab, test=test).exists():
            raise ValidationError("This test is already added for this lab.")

        lab_test = LabTest(
            lab=lab,
            test=test,
            price=price,
            test_image=test_image
        )

        if commit:
            lab_test.save()

        return lab_test


LabTestFormSet = modelformset_factory(
    LabTest,
    form=LabTestForm,
    extra=1,
    can_delete=True
)


# ======================================================
# 🔒 OTP Verification Form (Professional Version)
# ======================================================

class OTPVerificationForm(forms.Form):

    email = forms.EmailField(
        label="Registered Email",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Registered Email'
        })
    )

    otp = forms.CharField(
        max_length=6,
        label="Enter OTP",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'inputmode': 'numeric',
            'placeholder': '6-digit OTP'
        })
    )

    def clean_otp(self):
        otp = self.cleaned_data.get('otp')

        if not otp.isdigit():
            raise ValidationError("OTP must contain digits only.")

        if len(otp) != 6:
            raise ValidationError("OTP must be 6 digits.")

        return otp