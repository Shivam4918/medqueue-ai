from django.urls import path
from .views import hospital_admin_dashboard

urlpatterns = [
    path("dashboard/", hospital_admin_dashboard, name="hospital-admin-dashboard"),
]
