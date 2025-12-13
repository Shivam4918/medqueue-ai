# token_queue/models.py
from django.db import models
from django.utils import timezone

from hospitals.models import Hospital
from doctors.models import Doctor
from patients.models import Patient


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
        related_name="queue_tokens"
    )

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name="queue_tokens"
    )

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="queue_tokens"
    )

    token_number = models.PositiveIntegerField(editable=False)

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

    # ✅ FIX: add timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.token_number:
            last_token = Token.objects.filter(
                doctor=self.doctor
            ).order_by('-token_number').first()

            self.token_number = 1 if not last_token else last_token.token_number + 1

        super().save(*args, **kwargs)
    class Meta:
        ordering = ["booked_at"]
        unique_together = ["doctor", "booked_at", "token_number"]

    def __str__(self):
        return f"Token {self.token_number} - {self.doctor.name}"

