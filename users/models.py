from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ("patient", "Patient"),
        ("doctor", "Doctor"),
        ("receptionist", "Receptionist"),
        ("hospital_admin", "Hospital Admin"),
    ]

    phone = models.CharField(max_length=15, unique=True, null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="patient")

    # Hospital relation (only for staff roles)
    # temporarily remove hospital FK to avoid checks-instantiation issue
    # hospital = models.ForeignKey(
    #     "hospitals.Hospital",
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True
    # )
    
    def __str__(self):
        return f"{self.username} ({self.role})"
