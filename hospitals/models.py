# hospitals/models.py
from django.db import models
from django.conf import settings


class Hospital(models.Model):

    name = models.CharField(max_length=200)
    address = models.TextField(blank=True)

    contact_phone = models.CharField(max_length=20)

    city = models.CharField(max_length=100, blank=True)

    
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={"role": "hospital_admin"},
        related_name="managed_hospitals"
    )

    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    timezone = models.CharField(max_length=64, default="UTC")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} — {self.city}"