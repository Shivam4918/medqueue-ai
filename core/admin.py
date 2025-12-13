# core/admin.py
from django.contrib import admin
from .models import Token


@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    list_display = (
        'hospital',
        'doctor',
        'patient',
        'number',
        'status',
        'is_emergency',
        'queued_at',
    )
    list_filter = ('status', 'is_emergency', 'doctor', 'hospital')
    search_fields = ('number',)
