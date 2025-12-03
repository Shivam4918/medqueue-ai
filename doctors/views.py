from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, SAFE_METHODS
from .models import Doctor
from .serializers import DoctorSerializer
from .permissions import IsHospitalAdminOrSuperuser, IsDoctorOwnerOrHospitalAdminOrSuperuser

class DoctorViewSet(viewsets.ModelViewSet):
    """
    - GET (list/retrieve): AllowAny (public); change to IsAuthenticated if you prefer
    - POST (create): only HospitalAdmin or superuser
    - PUT/PATCH/DELETE: superuser or hospital admin OR the doctor who owns the record
    """
    queryset = Doctor.objects.select_related("user", "hospital").all()
    serializer_class = DoctorSerializer

    def get_permissions(self):
        method = self.request.method

        # public read
        if method in SAFE_METHODS:
            return [AllowAny()]

        # create -> only hospital admin or superuser
        if method == "POST":
            return [IsAuthenticated(), IsHospitalAdminOrSuperuser()]

        # updates/deletes -> object-level permission (checked in has_object_permission)
        if method in ("PUT", "PATCH", "DELETE"):
            return [IsAuthenticated(), IsDoctorOwnerOrHospitalAdminOrSuperuser()]

        # fallback: authenticated
        return [IsAuthenticated()]

    def get_queryset(self):
        user = getattr(self.request, "user", None)
        # doctors should only see their own record when listing (optional)
        if user and user.is_authenticated and getattr(user, "role", None) == "doctor":
            return self.queryset.filter(user_id=user.id)
        return self.queryset

    def perform_create(self, serializer):
        """
        When a doctor record is created by a hospital_admin or superuser,
        optionally ensure the linked User has role='doctor'.
        """
        instance = serializer.save()
        # ensure linked user's role is doctor
        try:
            user = instance.user
            if getattr(user, "role", None) != "doctor":
                user.role = "doctor"
                user.save(update_fields=["role"])
        except Exception:
            pass
        return instance

    def perform_update(self, serializer):
        instance = serializer.save()
        # keep user's role as 'doctor' after update
        try:
            user = instance.user
            if getattr(user, "role", None) != "doctor":
                user.role = "doctor"
                user.save(update_fields=["role"])
        except Exception:
            pass
        return instance
