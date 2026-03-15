# dashboard/urls.py

from django.urls import path
from .views import queue_live_view,patient_tokens_view,book_token_view,visit_history_view,profile_view,nearby_hospitals_view

from .views import (
    # Hospital admin / staff
    hospital_dashboard,
    hospital_detail_dashboard,
    hospital_analytics_dashboard,

    # Patient
    patient_dashboard,
    view_token_page,
    patient_queue_status,

    # Doctor
    doctor_dashboard,
    doctor_queue_page,
    doctor_call_token,
    doctor_complete_token,
    doctor_skip_token,

    # Receptionist
    receptionist_walkin_page,
    receptionist_queue_page,
    receptionist_dashboard
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

    path(
        "patient/tokens/",
        patient_tokens_view,
        name="patient_tokens",
    ),

    path(
        "patient/book-token/",
        book_token_view,
        name="book_token",
    ),

    path(
        "patient/visit-history/",
        visit_history_view,
        name="visit_history"
    ),

    path(
        "patient/profile/",
        profile_view,
        name="profile"
    ),

    path(
        "nearby-hospitals/",
        nearby_hospitals_view,
        name="nearby_hospitals"
    ),

    path(
        "patient/token/<int:token_id>/",
        view_token_page,
        name="view_token"
    ),

    path(
        "patient/queue-status/",
        patient_queue_status,
        name="patient_queue_status"
    ),

    #live queue
     path("queue/live/", queue_live_view, name="queue_live_view"),

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

    path(
        "doctor/token/<int:token_id>/call/",
        doctor_call_token,
        name="doctor_call_token"
    ),

    path(
        "doctor/token/<int:token_id>/complete/",
        doctor_complete_token,
        name="doctor_complete_token"
    ),

    path(
        "doctor/token/<int:token_id>/skip/",
        doctor_skip_token,
        name="doctor_skip_token"
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

    path(
        "receptionist/",
        receptionist_dashboard,
        name="receptionist_dashboard"
    )
]
