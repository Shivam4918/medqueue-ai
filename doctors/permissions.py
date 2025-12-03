from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsHospitalAdminOrSuperuser(BasePermission):
    """
    Allow access only to users with role == 'hospital_admin' or Django superusers.
    Use this for simple view-level checks (e.g. allowing hospital admins to create resources).
    """
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return getattr(user, "role", None) == "hospital_admin"


class IsDoctorOwnerOrHospitalAdminOrSuperuser(BasePermission):
    """
    Object-level permission for Doctor objects:

    - Superuser: allowed
    - Hospital admin: allowed (can manage doctors)
    - Doctor: allowed only when they own the Doctor record (doctor.user == request.user)
    - Others: denied

    This class implements has_object_permission. Use it for PUT/PATCH/DELETE on doctor endpoints.
    """
    def has_object_permission(self, request, view, obj):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False

        # superuser always allowed
        if user.is_superuser:
            return True

        # hospital admins allowed (optionally later we can restrict to admins of the same hospital)
        if getattr(user, "role", None) == "hospital_admin":
            return True

        # allow doctor to act on their own doctor record only
        if getattr(user, "role", None) == "doctor":
            # Use user id comparisons to avoid triggering DB fetches in some contexts
            try:
                return obj.user_id == user.id
            except Exception:
                return getattr(obj, "user", None) == user

        return False


class IsHospitalAdminForOwnHospitalOrReadOnly(BasePermission):
    """
    - SAFE_METHODS: allowed to everyone (or you can change to require auth)
    - For write methods: allow if user is superuser OR
      user.role == 'hospital_admin' AND user's hospital == object's hospital

    This is useful when hospital admins should only manage resources belonging to their hospital.
    It supports:
      - view-level check (has_permission) to block unauthenticated writes
      - object-level check (has_object_permission) to verify ownership
    """
    def has_permission(self, request, view):
        # allow reads
        if request.method in SAFE_METHODS:
            return True

        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        return getattr(user, "role", None) == "hospital_admin"

    def has_object_permission(self, request, view, obj):
        # allow reads
        if request.method in SAFE_METHODS:
            return True

        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        # If your User model has a `hospital` FK, compare it; otherwise adjust accordingly.
        user_hospital = getattr(user, "hospital", None)
        if user_hospital is None:
            return False

        # obj should have .hospital_id (most models do); fall back to obj.hospital
        try:
            return obj.hospital_id == getattr(user_hospital, "id", None)
        except Exception:
            return getattr(obj, "hospital", None) == user_hospital
