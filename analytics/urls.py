from django.urls import path
from .views import hospital_admin_dashboard
from .views import export_reports

urlpatterns = [
    path("dashboard/", hospital_admin_dashboard, name="hospital-admin-dashboard"),
    path("export/", export_reports, name="analytics-export"),
]
