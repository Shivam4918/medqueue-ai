# token_queue/models.py
from django.db import models
from django.utils import timezone
import string

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
        ("cancelled", "Cancelled"),
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

    # NEW PREFIX FIELD
    prefix = models.CharField(
        max_length=5,
        editable=False,
        blank=True
    )

    booked_at = models.DateTimeField(default=timezone.now)

    called_at = models.DateTimeField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="waiting"
    )

    priority = models.IntegerField(
        choices=PRIORITY_CHOICES,
        default=0
    )

    source = models.CharField(
        max_length=20,
        choices=[
            ("online", "Online Booking"),
            ("walkin", "Walk-in"),
            ("kiosk", "Self Kiosk"),
        ],
        default="online"
    )

    qr_code = models.ImageField(
        upload_to="token_qr/",
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # --------------------------------------------------
    # TOKEN DISPLAY (A-1, B-3 etc.)
    # --------------------------------------------------

    @property
    def display_token(self):
        return f"{self.prefix}-{self.token_number}"

    # --------------------------------------------------
    # DOCTOR PREFIX GENERATION
    # --------------------------------------------------

    def get_doctor_prefix(self):

        doctors = Doctor.objects.filter(
            hospital=self.hospital,
            is_active=True
        ).order_by("id")

        doctor_list = list(doctors)

        index = doctor_list.index(self.doctor)

        letters = string.ascii_uppercase

        return letters[index]
    # --------------------------------------------------
    # QR CODE GENERATION
    # --------------------------------------------------

    def generate_qr(self):

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
    # SAVE LOGIC
    # --------------------------------------------------

    def save(self, *args, **kwargs):

        is_new = self.pk is None

        if not self.token_number:

            today = timezone.localdate()

            last_token = Token.objects.filter(
                doctor=self.doctor,
                booked_at__date=today
            ).order_by("-token_number").first()

            self.token_number = (
                1 if not last_token else last_token.token_number + 1
            )

        # assign doctor prefix
        if not self.prefix:
            self.prefix = self.get_doctor_prefix()

        super().save(*args, **kwargs)

        # generate QR after ID exists
        if is_new and not self.qr_code:
            self.generate_qr()
            super().save(update_fields=["qr_code"])

    class Meta:
        ordering = ["token_number"]
        unique_together = ["doctor", "token_number", "booked_at"]

    def __str__(self):
        return f"{self.prefix}-{self.token_number} ({self.doctor})"