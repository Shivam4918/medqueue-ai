from .models import Patient

def get_or_create_patient_from_user(user):
    patient, _ = Patient.objects.get_or_create(
        user=user,
        defaults={
            "name": user.get_full_name() or user.username,
            "phone": user.phone or ""
        }
    )
    return patient
