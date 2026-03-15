# doctors/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DoctorViewSet, DoctorDelayAPIView, doctors_by_hospital


router = DefaultRouter()
router.register(r"doctors", DoctorViewSet, basename="doctors")

urlpatterns = [
    path("hospital/<int:hospital_id>/doctors/",doctors_by_hospital),
    
    path("doctor/<int:doctor_id>/delay/", DoctorDelayAPIView.as_view()),

    path("", include(router.urls)),

    
    
]
