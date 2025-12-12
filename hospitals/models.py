# hospitals/models.py
from django.db import models

class Hospital(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField(blank=True)

    # keep the real DB column name here
    contact_number = models.CharField(max_length=30, blank=True, null=True)

    # backwards-compatible alias for code that expects contact_phone
    @property
    def contact_phone(self):
        return self.contact_number or ""

    @contact_phone.setter
    def contact_phone(self, value):
        self.contact_number = value

    city = models.CharField(max_length=100, blank=True)
    timezone = models.CharField(max_length=64, default="UTC")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        db_table = 'core_hospital'

    def __str__(self) -> str:
        return f"{self.name} — {self.city}"
