# token_queue/models.py
from django.db import models
from django.utils import timezone

# ✅ NEW IMPORTS (QR SUPPORT)
from django.core.files.base import ContentFile
import qrcode
import json
from io import BytesIO

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

    # ✅ NEW FIELD — QR CODE IMAGE
    qr_code = models.ImageField(
        upload_to="token_qr/",
        blank=True,
        null=True
    )

    # timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # --------------------------------------------------
    # QR GENERATION LOGIC
    # --------------------------------------------------
    def generate_qr(self):
        """
        Generates QR code containing token verification data
        """
        data = {
            "token_id": self.id,
            "hospital_id": self.hospital.id,
            "doctor_id": self.doctor.id
        }

        qr = qrcode.make(json.dumps(data))
        buffer = BytesIO()
        qr.save(buffer, format="PNG")

        filename = f"token_{self.id}.png"
        self.qr_code.save(
            filename,
            ContentFile(buffer.getvalue()),
            save=False
        )

    # --------------------------------------------------
    # SAVE OVERRIDE
    # --------------------------------------------------
    def save(self, *args, **kwargs):
        is_new = self.pk is None

        # Token number generation (YOUR EXISTING LOGIC)
        if not self.token_number:
            last_token = Token.objects.filter(
                doctor=self.doctor
            ).order_by("-token_number").first()

            self.token_number = 1 if not last_token else last_token.token_number + 1

        # First save (to get self.id)
        super().save(*args, **kwargs)

        # Generate QR only once (after ID exists)
        if is_new and not self.qr_code:
            self.generate_qr()
            super().save(update_fields=["qr_code"])

    class Meta:
        ordering = ["booked_at"]
        unique_together = ["doctor", "booked_at", "token_number"]

    def __str__(self):
        return f"Token {self.token_number} - {self.doctor}"
