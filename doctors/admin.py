# doctors/admin.py
from django.contrib import admin
from .models import Doctor
from hospitals.models import Hospital as HospHospital
@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    # Use actual fields present on doctors.models.Doctor
    list_display = ("name", "hospital", "speciality", "opd_start", "opd_end", "is_active")
    search_fields = ("name", "speciality", "hospital__name")
    list_filter = ("hospital", "is_active")
    # no 'user' field present — use hospital as raw id for faster admin if desired
    raw_id_fields = ("hospital",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "hospital":
            kwargs["queryset"] = HospHospital.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)