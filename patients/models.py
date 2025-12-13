# patients/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Patient(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='patient_profile',
        null=True,
        blank=True
    )
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    dob = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'core_patient'   # IMPORTANT: keeps existing DB table
        ordering = ['name']

    def __str__(self):
        return self.name
