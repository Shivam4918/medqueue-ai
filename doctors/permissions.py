from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsHospitalAdminForOwnHospitalOrReadOnly(BasePermission):
    """
    - Safe methods allowed to anyone (or you can require authentication).
    - For write methods: allow if user is superuser OR user.role == 'hospital_admin' AND user's hospital == object's hospital (or hospital in POST data).
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True

        return getattr(user, "role", None) == "hospital_admin"

    def has_object_permission(self, request, view, obj):
        # read allowed
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        if user.is_superuser:
            return True

        # If hospital is on the user model (user.hospital), compare
        user_hospital = getattr(user, "hospital", None)
        return user_hospital is not None and obj.hospital_id == getattr(user_hospital, "id", None)
