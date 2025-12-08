# doctors/admin.py
from django.contrib import admin
from .models import Doctor

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    # make sure these fields exist on your Doctor model; change names if necessary
    list_display = ("user", "hospital", "specialization", "opd_start", "opd_end", "is_active")
    search_fields = ("user__username", "user__email", "specialization", "hospital__name")
    list_filter = ("hospital", "is_active")
    raw_id_fields = ("user", "hospital")
