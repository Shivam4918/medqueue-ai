from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import random

def generate_otp():
    """Return a 6-digit numeric OTP as a string."""
    return f"{random.randint(100000, 999999):06d}"


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


class OTP(models.Model):
    """
    Simple OTP model for phone-based authentication.
    - phone: phone number string
    - otp: the 6-digit code
    - created_at: timestamp when generated
    - is_used: mark as consumed after verification
    """
    phone = models.CharField(max_length=15, db_index=True)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=timezone.now)
    is_used = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["phone", "is_used"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.phone} — {self.otp} (used={self.is_used})"
