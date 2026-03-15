from django.urls import path
from .views import (
    SendOTPView,
    VerifyOTPView,
    notification_list,
    notification_count,
    mark_notifications_read,
    patient_notifications,
    portal_login,
    patient_register,
    verify_email_otp,
    check_user_exists,
    resend_otp,
    password_reset_request,
    password_reset_confirm,
    password_reset_done
)

app_name = "users"

urlpatterns = [
    # ======================
    # OTP AUTH (API)
    # ======================
    path("send-otp/", SendOTPView.as_view(), name="send-otp"),
    path("verify-otp/", VerifyOTPView.as_view(), name="verify-otp"),
    path("resend-otp/", resend_otp, name="resend_otp"),

    path("patient/verify-otp/", verify_email_otp, name="verify_email_otp"),

    # ======================
    # Password Reset (WEB)
    # ======================
    path("password-reset/", password_reset_request, name="password_reset"),
    path("password-reset/done/", password_reset_done, name="password_reset_done"),
    path("password-reset-confirm/<uidb64>/<token>/", password_reset_confirm, name="password_reset_confirm"),


    # ======================
    # Patient Register (WEB)
    # ======================
    path("patient/register/", patient_register, name="patient_register"),
    path("check-user/", check_user_exists, name="check_user_exists"),
    path("notifications/",patient_notifications, name="patient_notifications"),


    # ======================
    # Notifications
    # ======================
    path("notifications/read/", mark_notifications_read, name="notifications-read"),
    path(
        "notifications/count/",
        notification_count,
        name="notification_count"
    ),

    # ======================
    # Portal-based Login (WEB)
    # ======================
    path("patient/login/", portal_login, {"portal": "patient"}, name="patient_login"),
    path("doctor/login/", portal_login, {"portal": "doctor"}, name="doctor_login"),
    path("receptionist/login/", portal_login, {"portal": "receptionist"}, name="reception_login"),
    path("hospital/login/", portal_login, {"portal": "hospital"}, name="hospital_login"),

     # ======================
    # Portal-based Login (WEB)
    # ======================
]
