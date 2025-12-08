from django.contrib import admin
from .models import Hospital, Patient, Token

@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_number', 'created_at')
    search_fields = ('name',)

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone')
    search_fields = ('name', 'phone')

@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    list_display = ('hospital', 'doctor', 'number', 'status', 'is_emergency', 'queued_at')
    list_filter = ('status', 'is_emergency', 'doctor')
    search_fields = ('number',)
