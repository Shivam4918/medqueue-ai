#doctors/models.py

from django.db import models
from django.conf import settings

class Doctor(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="doctor_profile",
        null=True,
        blank=True
    )

    hospital = models.ForeignKey(
        "hospitals.Hospital",
        on_delete=models.CASCADE,
        related_name="doctors"
    )

    name = models.CharField(max_length=255)
    speciality = models.CharField(max_length=255, blank=True)

    opd_start = models.TimeField(null=True, blank=True)
    opd_end = models.TimeField(null=True, blank=True)

    profile_picture = models.ImageField(
        upload_to="doctor_profiles/",
        null=True,
        blank=True
    )

    is_active = models.BooleanField(default=True)
    is_paused = models.BooleanField(default=False)

    def __str__(self):
        return self.name
