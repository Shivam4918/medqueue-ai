from django.urls import path
from .admin_views import superadmin_dashboard

urlpatterns = [

    path(
        "admin/dashboard/",
        superadmin_dashboard,
        name="superadmin_dashboard"
    ),

]