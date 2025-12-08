# core/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Hospital(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    contact_number = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile', null=True, blank=True)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    dob = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.name


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

    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='tokens')
    # doctor now references the Doctor model in the doctors app using the string form
    doctor = models.ForeignKey('doctors.Doctor', on_delete=models.CASCADE, related_name='tokens')
    patient = models.ForeignKey(Patient, on_delete=models.SET_NULL, null=True, blank=True, related_name='tokens')
    number = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_WAITING)
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
        # protect if doctor is a string-repr
        doctor_name = getattr(self.doctor, "name", str(self.doctor))
        return f"{self.hospital.name} - {doctor_name} #{self.number}"
