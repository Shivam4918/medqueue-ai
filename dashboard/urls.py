# dashboard/urls.py
from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView

from .views import (
    DashboardHomeView,
    HospitalDetailView,
    patient_token_page,
    doctor_queue_page,
    receptionist_walkin_page,
)

app_name = "dashboard"

urlpatterns = [
    # ---------- Authentication ----------
    path("login/", LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),

    # ---------- Admin / Staff Dashboard ----------
    path("", DashboardHomeView.as_view(), name="home"),
    path("hospital/<int:pk>/", HospitalDetailView.as_view(), name="hospital-detail"),

    # ---------- New Pages (DAY 6) ----------
    path("patient/", patient_token_page, name="patient-token"),
    path("doctor/", doctor_queue_page, name="doctor-queue"),
    path("receptionist/walkin/", receptionist_walkin_page, name="walkin"),
]
