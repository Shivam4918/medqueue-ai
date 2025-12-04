# token_queue/views.py
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response

from users.permissions import IsReceptionist, IsDoctor
from .models import Token
from .serializers import TokenSerializer, TokenCreateSerializer
from .services import create_token, estimate_wait_for_token


class TokenViewSet(viewsets.ModelViewSet):
    """
    Admin/Receptionist/Doctor interface (existing).
    Only staff roles should be able to create/manage tokens here.
    """
    queryset = Token.objects.all().order_by("-booked_at")
    serializer_class = TokenSerializer
    permission_classes = [IsReceptionist | IsDoctor]


class CreateTokenAPIView(APIView):
    """
    Public endpoint for a patient to book a token.
    Accepts patient_id OR phone (phone will create/find a patient).
    Returns created token + estimated wait & ETA (local time).
    """
    permission_classes = []  # open endpoint

    def post(self, request):
        serializer = TokenCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        patient = data["patient"]
        doctor = data["doctor"]
        hospital = data["hospital"]
        priority = data.get("priority", 0)

        token = create_token(patient=patient, doctor=doctor, hospital=hospital, priority=priority)

        minutes, eta_dt = estimate_wait_for_token(doctor.id, token.token_number)

        return Response({
            "token_id": token.id,
            "token_number": token.token_number,
            "status": token.status,
            "priority": token.priority,
            "estimated_wait_minutes": minutes,
            "eta": timezone.localtime(eta_dt).isoformat()
        }, status=status.HTTP_201_CREATED)
