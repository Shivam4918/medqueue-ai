from django.contrib import admin
from .models import Doctor

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("user", "hospital", "specialization", "opd_start", "opd_end")
    search_fields = ("user__username", "user__email", "specialization", "hospital__name")
    raw_id_fields = ("user", "hospital")
