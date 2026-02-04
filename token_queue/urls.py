# token_queue/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    TokenViewSet,
    CreateTokenAPIView,
    TokenBookAPIView,
    WalkinTokenAPIView,
    DoctorQueueAPIView,
    TokenCallAPIView,
    TokenCompleteAPIView,
    TokenSkipAPIView,
    TokenPriorityAPIView,
    patient_dashboard,
    patient_token_history,
    VerifyTokenAPIView,
    DoctorDelayAPIView
)

# Router for admin/receptionist/doctor CRUD in DRF UI
router = DefaultRouter()
router.register("", TokenViewSet, basename="token")

urlpatterns = [
    # DRF browseable token list/manage
    path("", include(router.urls)),

    # Admin/Receptionist token creation (old flow)
    path("create/", CreateTokenAPIView.as_view(), name="token-create"),

    # Patient online booking
    path("book/", TokenBookAPIView.as_view(), name="token-book"),

    # Walk-in token creation (receptionist only)
    path("walkin/", WalkinTokenAPIView.as_view(), name="token-walkin"),

    # Doctor queue — active tokens (waiting + in_service)
    path("doctors/<int:doctor_id>/queue/", DoctorQueueAPIView.as_view(), name="doctor-queue"),
    path("doctors/<int:doctor_id>/delay/", DoctorDelayAPIView.as_view()),


    # Token actions (call, complete, skip, priority)
    path("patient/home/", patient_dashboard, name="patient-dashboard"),
    path("tokens/<int:pk>/call/", TokenCallAPIView.as_view(), name="token-call"),
    path("tokens/<int:pk>/complete/", TokenCompleteAPIView.as_view(), name="token-complete"),
    path("tokens/<int:pk>/skip/", TokenSkipAPIView.as_view(), name="token-skip"),
    path("tokens/<int:pk>/priority/", TokenPriorityAPIView.as_view(), name="token-priority"),
    path("patient/history/", patient_token_history, name="patient-token-history"),

    path("tokens/verify/<int:token_id>/", VerifyTokenAPIView.as_view(), name="token-verify"),

]
