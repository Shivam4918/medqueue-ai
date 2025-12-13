# hospitals/models.py
from django.db import models

class Hospital(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField(blank=True)

    # Map model field to the existing DB column contact_number.
    contact_phone = models.CharField(max_length=20)


    # Backwards-compatible property if some code still reads contact_number
    @property
    def contact_number(self):
        return self.contact_phone or ""

    @contact_number.setter
    def contact_number(self, value):
        self.contact_phone = value

    city = models.CharField(max_length=100, blank=True)
    timezone = models.CharField(max_length=64, default="UTC")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # class Meta:
    #     ordering = ["name"]
    #     db_table = 'core_hospital'

    def __str__(self) -> str:
        return f"{self.name} — {self.city}"
