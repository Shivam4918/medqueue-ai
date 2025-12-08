# doctors/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, SAFE_METHODS

from .models import Doctor
from .serializers import DoctorSerializer
from .permissions import (
    IsHospitalAdminOrSuperuser,
    IsDoctorOwnerOrHospitalAdminOrSuperuser
)

class DoctorViewSet(viewsets.ModelViewSet):
    """
    Doctor management:
    - GET (list/retrieve): public (AllowAny) or switch to IsAuthenticated if needed.
    - POST: only HospitalAdmin or Superuser.
    - PUT/PATCH/DELETE: HospitalAdmin, Superuser, or Doctor who owns the profile.
    """
    queryset = Doctor.objects.select_related("user", "hospital").all()
    serializer_class = DoctorSerializer

    def get_permissions(self):
        method = self.request.method

        # Read operations (GET)
        if method in SAFE_METHODS:
            return [AllowAny()]

        # Create doctor
        if method == "POST":
            return [IsAuthenticated(), IsHospitalAdminOrSuperuser()]

        # Modify doctor
        if method in ("PUT", "PATCH", "DELETE"):
            return [IsAuthenticated(), IsDoctorOwnerOrHospitalAdminOrSuperuser()]

        return [IsAuthenticated()]

    def get_queryset(self):
        user = getattr(self.request, "user", None)

        # If the logged-in user is a doctor, return only their own record
        if user and user.is_authenticated and getattr(user, "role", None) == "doctor":
            return self.queryset.filter(user_id=user.id)

        return self.queryset

    def perform_create(self, serializer):
        instance = serializer.save()

        # Ensure assigned user has role="doctor"
        user = instance.user
        if getattr(user, "role", None) != "doctor":
            user.role = "doctor"
            user.save(update_fields=["role"])

        return instance

    def perform_update(self, serializer):
        instance = serializer.save()

        # Keep user's role as doctor
        user = instance.user
        if getattr(user, "role", None) != "doctor":
            user.role = "doctor"
            user.save(update_fields=["role"])

        return instance
