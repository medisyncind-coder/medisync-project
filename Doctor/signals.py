from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import User
from Doctor.models import Patient

@receiver(post_save, sender=User)
def create_patient_profile(sender, instance, created, **kwargs):
    if created:
        Patient.objects.create(
            user=instance,
            name=instance.first_name
        )