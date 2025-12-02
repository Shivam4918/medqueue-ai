from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from .models import Doctor
from .serializers import DoctorSerializer
from .permissions import IsHospitalAdminForOwnHospitalOrReadOnly

class DoctorViewSet(viewsets.ModelViewSet):
    queryset = Doctor.objects.select_related("user", "hospital").all()
    serializer_class = DoctorSerializer
    permission_classes = [IsHospitalAdminForOwnHospitalOrReadOnly]

    def perform_create(self, serializer):
        user = self.request.user
        if user.is_superuser:
            serializer.save()
            return

        # hospital_admin flow: ensure user has hospital attribute
        if getattr(user, "role", None) == "hospital_admin":
            user_hospital = getattr(user, "hospital", None)
            if not user_hospital:
                raise PermissionDenied("Hospital admin must be assigned to a hospital.")
            # if client sent a different hospital, block it
            sent_hospital = serializer.validated_data.get("hospital")
            if sent_hospital and sent_hospital.id != user_hospital.id:
                raise PermissionDenied("You can only add doctors to your own hospital.")
            serializer.save(hospital=user_hospital)
            return

        raise PermissionDenied("Only hospital admins or superusers can create doctors.")

    def perform_update(self, serializer):
        # reuse same permission logic: object permission already checks hospital ownership
        serializer.save()
        linked_user = serializer.instance.user
        if linked_user.role != 'doctor':
            linked_user.role = 'doctor'
            linked_user.save(update_fields=['role'])