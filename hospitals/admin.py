from django.contrib import admin
from .models import Hospital

@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "contact_phone", "timezone", "created_at")
    search_fields = ("name", "city", "address", "contact_phone")
