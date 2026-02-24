# dashboard/urls.py

from django.urls import path

from .views import (
    # Hospital admin / staff
    hospital_dashboard,
    hospital_detail_dashboard,
    hospital_analytics_dashboard,

    # Patient
    patient_dashboard,

    # Doctor
    doctor_dashboard,
    doctor_queue_page,

    # Receptionist
    receptionist_walkin_page,
    receptionist_queue_page,
)

app_name = "dashboard"

urlpatterns = [

    # =====================================================
    # 🏥 HOSPITAL ADMIN (ROLE: hospital_admin)
    # =====================================================

    # Hospital list (main admin dashboard)
    path("hospital/", hospital_dashboard, name="hospital_dashboard"),

    # Hospital detail
    path(
        "hospital/<int:pk>/",
        hospital_detail_dashboard,
        name="hospital_detail",
    ),

    # Hospital analytics (MongoDB)
    path(
        "hospital/<int:hospital_id>/analytics/",
        hospital_analytics_dashboard,
        name="hospital_analytics",
    ),

    # =====================================================
    # 👤 PATIENT (ROLE: patient)
    # =====================================================

    path(
        "patient/",
        patient_dashboard,
        name="patient_dashboard",
    ),

    # =====================================================
    # 👨‍⚕️ DOCTOR (ROLE: doctor)
    # =====================================================

    # Main doctor dashboard
    path(
        "doctor/",
        doctor_dashboard,
        name="doctor_dashboard",
    ),

    # Legacy / queue page (kept for JS compatibility)
    path(
        "doctor/queue/",
        doctor_queue_page,
        name="doctor_queue",
    ),

    # =====================================================
    # 🧾 RECEPTIONIST (ROLE: receptionist)
    # =====================================================

    path(
        "receptionist/walkin/",
        receptionist_walkin_page,
        name="receptionist_walkin",
    ),

    path(
        "receptionist/queue/",
        receptionist_queue_page,
        name="receptionist_queue",
    ),
]
