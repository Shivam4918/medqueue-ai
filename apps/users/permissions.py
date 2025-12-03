from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsHospitalAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.role == "hospital_admin")


class IsDoctor(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.role == "doctor")


class IsReceptionist(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.role == "receptionist")


class IsPatient(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.role == "patient")
