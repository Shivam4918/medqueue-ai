# doctors/models.py
from django.db import models

class Doctor(models.Model):
    # Fields copied exactly from OLD core.models.Doctor
    hospital = models.ForeignKey("hospitals.Hospital", on_delete=models.CASCADE, related_name='doctors')
    name = models.CharField(max_length=255)
    speciality = models.CharField(max_length=255, blank=True)
    opd_start = models.TimeField(null=True, blank=True)
    opd_end = models.TimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'core_doctor'   # <-- THE CRITICAL LINE
        ordering = ['name']

    def __str__(self):
        hospital_name = self.hospital.name if self.hospital_id and self.hospital else "No hospital"
        return f"{self.name} ({hospital_name})"
