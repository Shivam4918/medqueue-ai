# core/models.py
from django.db import models


class Token(models.Model):
    STATUS_WAITING = 'waiting'
    STATUS_CALLED = 'called'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_WAITING, 'Waiting'),
        (STATUS_CALLED, 'Called'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    hospital = models.ForeignKey(
        'hospitals.Hospital',
        on_delete=models.CASCADE,
        related_name='core_tokens'
    )

    doctor = models.ForeignKey(
        'doctors.Doctor',
        on_delete=models.CASCADE,
        related_name='core_tokens'
    )

    patient = models.ForeignKey(
        'patients.Patient',   # 🔥 UPDATED
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tokens'
    )

    number = models.PositiveIntegerField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_WAITING
    )
    queued_at = models.DateTimeField(auto_now_add=True)
    called_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_emergency = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['queued_at']
        indexes = [
            models.Index(fields=['doctor', 'status']),
        ]

    def __str__(self):
        doctor_name = getattr(self.doctor, "name", str(self.doctor))
        return f"{self.hospital.name} - {doctor_name} #{self.number}"
