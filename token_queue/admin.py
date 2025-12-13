from django.contrib import admin
from .models import Token

@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    list_display = ("id", "hospital", "doctor", "patient", "status", "created_at")
    list_filter = ("status", "priority")
    search_fields = ("patient__user__username",)


    # Add readonly fields only if present
    readonly = []
    if hasattr(Token, "created_at"):
        readonly.append("created_at")
    if hasattr(Token, "updated_at"):
        readonly.append("updated_at")
    readonly_fields = tuple(readonly)