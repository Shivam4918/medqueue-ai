from django.urls import path
from .views import (
    nearby_hospitals, 
    hospital_detail, 
    create_hospital, 
    hospital_dashboard,
    hospital_doctors,
    add_doctor,
    edit_doctor,
    disable_doctor,
    hospital_staff,
    add_receptionist,
    disable_receptionist
)

urlpatterns = [

    # Nearby hospitals list
    path("nearby/", nearby_hospitals, name="nearby_hospitals"),

    # Hospital detail page
    path("<int:pk>/", hospital_detail, name="hospital_detail"),

    # Create hospital (super admin)
    path("create/", create_hospital, name="create_hospital"),

    # Hospital admin dashboard
    path("dashboard/", hospital_dashboard, name="hospital_dashboard"),
    path("staff/", hospital_staff, name="hospital_staff"),
    path("staff/add/", add_receptionist, name="add_receptionist"),
    path("staff/<int:user_id>/disable/", disable_receptionist, name="disable_receptionist"),
    
    # doctor management
    path("doctors/", hospital_doctors, name="hospital_doctors"),
    path("doctors/add/", add_doctor, name="add_doctor"),
    path("doctors/<int:doctor_id>/edit/", edit_doctor, name="edit_doctor"),
    path("doctors/<int:doctor_id>/disable/", disable_doctor, name="disable_doctor"),
]