# core/urls.py

from django.urls import path
# from .views import public_home
from .admin_views import superadmin_dashboard

app_name = "core"

urlpatterns = [
    path(
        "admin/dashboard/",
        superadmin_dashboard,
        name="superadmin_dashboard"
    ),

]
