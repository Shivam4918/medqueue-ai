from rest_framework.permissions import BasePermission

class IsHospitalAdmin(BasePermission):
    """Allow only hospital_admin role or Django superusers."""
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return getattr(user, "role", None) == "hospital_admin"


class IsDoctor(BasePermission):
    """Allow only users with role == 'doctor' or superusers."""
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return getattr(user, "role", None) == "doctor"


class IsReceptionist(BasePermission):
    """Allow only users with role == 'receptionist' or superusers."""
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return getattr(user, "role", None) == "receptionist"


class IsPatient(BasePermission):
    """Allow only users with role == 'patient' or superusers."""
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        # allow superusers for admin/debugging convenience
        if user.is_superuser:
            return True
        return getattr(user, "role", None) == "patient"
