# users/constants.py

from django.db import models

class UserRole(models.TextChoices):
    SUPER_ADMIN = "super_admin", "Super Admin"
    PATIENT = "patient", "Patient"
    DOCTOR = "doctor", "Doctor"
    RECEPTIONIST = "receptionist", "Receptionist"
    HOSPITAL_ADMIN = "hospital_admin", "Hospital Admin"
