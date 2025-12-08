# doctors/models.py
from django.db import models

class Doctor(models.Model):
    # kept the original fields from core.models exactly so existing DB columns map 1:1
    hospital = models.ForeignKey('core.Hospital', on_delete=models.CASCADE, related_name='doctors')
    name = models.CharField(max_length=255)
    speciality = models.CharField(max_length=255, blank=True)
    opd_start = models.TimeField(null=True, blank=True)
    opd_end = models.TimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        # map to the existing table name used by the original model
        db_table = 'core_doctor'
        # you may keep ordering if you like
        # ordering = ['name']

    def __str__(self):
        # guard against missing hospital
        hospital_name = self.hospital.name if self.hospital_id and self.hospital else "No hospital"
        return f"{self.name} ({hospital_name})"
