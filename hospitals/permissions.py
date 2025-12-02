from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsHospitalAdminOrReadOnly(BasePermission):
    """
    Allow safe (GET/HEAD/OPTIONS) to everyone (authenticated).
    Only allow create/update/delete to users with role 'hospital_admin' or to superusers.
    """

    def has_permission(self, request, view):
        # Allow read-only to any request (you can require authentication if you prefer)
        if request.method in SAFE_METHODS:
            return True

        # Must be authenticated for write actions
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False

        # Superuser allowed
        if user.is_superuser:
            return True

        # Your custom user model has a 'role' field
        return getattr(user, "role", None) == "hospital_admin"
