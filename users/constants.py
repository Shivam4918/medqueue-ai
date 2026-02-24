from django.db import models

class UserRole(models.TextChoices):
    PATIENT = "patient", "Patient"
    DOCTOR = "doctor", "Doctor"
    RECEPTIONIST = "receptionist", "Receptionist"
    HOSPITAL_ADMIN = "hospital_admin", "Hospital Admin"
