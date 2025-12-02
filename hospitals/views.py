from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import Hospital
from .serializers import HospitalSerializer
from .permissions import IsHospitalAdminOrReadOnly

class HospitalViewSet(viewsets.ModelViewSet):
    queryset = Hospital.objects.all()
    serializer_class = HospitalSerializer

    # Allow read for everyone but restrict write to hospital_admin or superuser
    permission_classes = [IsHospitalAdminOrReadOnly]
    # permission_classes = [IsAuthenticated, IsHospitalAdminOrReadOnly]
