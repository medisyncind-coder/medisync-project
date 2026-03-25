from django import forms
from .models import Appointment, Payment, LabAppointment


class AppointmentForm(forms.ModelForm):

    class Meta:
        model = Appointment

        # Doctor, patient, slot date/time view set karega
        exclude = [
            "doctor",
            "patient",
            "booking_id",
            "status",
            "cancellation_reason",
            "prescription_file",
            "approved_at",
            "completed_at",
            "created_at",
            "appointment_date",
            "appointment_time",
            "is_paid",
            "payment_type", 
        ]

        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control"}),
            "age": forms.NumberInput(attrs={"class": "form-control"}),
            "gender": forms.Select(attrs={"class": "form-control"}),
            "contact_number": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "symptoms": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "existing_diseases": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "current_medications": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "allergies": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "consultation_mode": forms.Select(attrs={"class": "form-control"}),
            "payment_type": forms.Select(attrs={"class": "form-control"}),
        }


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["payment_method"]
        
        
class LabAppointmentForm(forms.ModelForm):

    class Meta:
        model = LabAppointment

        # Lab, patient, slot date/time view set karega
        exclude = [
            "lab",
            "patient",
            "booking_id",
            "status",
            "approved_at",
            "completed_at",
            "created_at",
            "appointment_date",
            "appointment_time",
            "is_paid",
            "payment_type",
            "report_file",
        ]

        widgets = {

            "full_name": forms.TextInput(
                attrs={"class": "form-control"}
            ),

            "age": forms.NumberInput(
                attrs={"class": "form-control"}
            ),

            "gender": forms.Select(
                attrs={"class": "form-control"}
            ),

            "contact_number": forms.TextInput(
                attrs={"class": "form-control"}
            ),

            "email": forms.EmailInput(
                attrs={"class": "form-control"}
            ),

            "address": forms.Textarea(
                attrs={"class": "form-control", "rows": 2}
            ),

            "test_name": forms.TextInput(
                attrs={"class": "form-control"}
            ),

            "notes": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),

            "sample_collection": forms.Select(
                attrs={"class": "form-control"}
            ),
        }