from django.urls import path
from .views import (
    SendOTPView,
    VerifyOTPView,
    notification_list,
    mark_notifications_read,
)

urlpatterns = [
    path("send-otp/", SendOTPView.as_view(), name="send-otp"),
    path("verify-otp/", VerifyOTPView.as_view(), name="verify-otp"),

    path("notifications/", notification_list, name="notifications"),
    path("notifications/read/", mark_notifications_read, name="notifications-read"),
]
