from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from .models import Notification

admin.site.register(User, UserAdmin)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "message", "is_read", "created_at")
    list_filter = ("is_read",)
