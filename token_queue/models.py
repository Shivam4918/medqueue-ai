from django.db import models
from django.utils import timezone

from hospitals.models import Hospital
from doctors.models import Doctor
from users.models import User


class Token(models.Model):
    STATUS_CHOICES = [
        ("waiting", "Waiting"),
        ("in_service", "In Service"),
        ("completed", "Completed"),
        ("skipped", "Skipped"),
    ]

    PRIORITY_CHOICES = [
        (0, "Normal"),
        (1, "Emergency"),
    ]

    hospital = models.ForeignKey(
        Hospital,
        on_delete=models.CASCADE,
        related_name="tokens"
    )

    doctor = models.ForeignKey(
        'doctors.Doctor',
        on_delete=models.CASCADE,
        related_name="queue_tokens"
    )

    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="patient_tokens"
    )

    token_number = models.PositiveIntegerField()

    booked_at = models.DateTimeField(default=timezone.now)
    called_at = models.DateTimeField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="waiting"
    )

    priority = models.IntegerField(
        choices=PRIORITY_CHOICES,
        default=0
    )

    class Meta:
        ordering = ["booked_at"]
        unique_together = ["doctor", "booked_at", "token_number"]

    def __str__(self):
        return f"Token #{self.token_number} — {self.doctor.user.username}"
