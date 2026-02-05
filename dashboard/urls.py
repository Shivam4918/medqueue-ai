# dashboard/urls.py
from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from .views import receptionist_queue_page

from .views import (
    DashboardHomeView,
    HospitalDetailView,
    patient_token_page,
    doctor_queue_page,
    receptionist_walkin_page,
    doctor_dashboard, 
    hospital_analytics_dashboard,         # ✅ ADD THIS
)

app_name = "dashboard"

urlpatterns = [
    # ---------- Authentication ----------
    path("login/", LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),

    # ---------- Admin / Staff Dashboard ----------
    path("", DashboardHomeView.as_view(), name="home"),
    path("hospital/<int:pk>/", HospitalDetailView.as_view(), name="hospital-detail"),

    # ---------- Patient ----------
    path("patient/", patient_token_page, name="patient-token"),

    # ---------- Doctor ----------
    path("doctor/", doctor_queue_page, name="doctor-queue"),                 # OLD (queue page)
    path("doctor/dashboard/", doctor_dashboard, name="doctor-dashboard"), 
       # ✅ NEW (Step 7)

    # ---------- Receptionist ----------
    path("receptionist/queue/", receptionist_queue_page, name="receptionist-queue"),
    path("receptionist/walkin/", receptionist_walkin_page, name="walking"),

    path(
    "hospital/<int:hospital_id>/analytics/",
    hospital_analytics_dashboard,
    name="hospital-analytics",
    ),

    
]
