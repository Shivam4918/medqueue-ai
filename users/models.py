from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import random
from .constants import UserRole

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
    # role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="patient")
    role = models.CharField(
    max_length=32,
    choices=UserRole.choices,
    null=True,
    blank=True
    )

    hospital = models.ForeignKey(
        "hospitals.Hospital",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="staff"
    )
    
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
    
class EmailOTP(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=10)

    
class Notification(models.Model):

    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    title = models.CharField(max_length=255, default="Notification")

    message = models.TextField()

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.title}"
    


