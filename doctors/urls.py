# doctors/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DoctorViewSet, DoctorDelayAPIView


router = DefaultRouter()
router.register(r"doctors", DoctorViewSet, basename="doctors")

urlpatterns = [
    path("doctor/<int:doctor_id>/delay/", DoctorDelayAPIView.as_view()),

    path("", include(router.urls)),
    
]
