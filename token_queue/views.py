# token_queue/views.py
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from users.permissions import IsReceptionist, IsDoctor
from users.models import User
from .models import Token
from .serializers import (
    TokenSerializer,
    TokenCreateSerializer,
    TokenBookingSerializer,
    WalkinTokenSerializer,
)
from .services import create_token, estimate_wait_for_token
from doctors.models import Doctor


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
    Admin-style open endpoint for creating tokens.
    Accepts patient_id OR phone (phone will create/find a patient).
    Returns created token + estimated wait & ETA (local time).
    Keep this open if your reception/admin UI calls it without a patient login.
    """
    permission_classes = []  # open endpoint (adjust if you want auth)

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


class TokenBookAPIView(APIView):
    """
    Patient-facing booking endpoint:
    POST /api/token_queue/book/
    Body: {"doctor_id": <id>}
    Requires authenticated patient user. (If you want anonymous booking by phone,
    set permission_classes = [] and use TokenBookingSerializer to accept 'phone'.)
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # role check: ensure only patients can book here
        if getattr(request.user, "role", None) != "patient":
            return Response({"detail": "Only patients may book tokens."}, status=status.HTTP_403_FORBIDDEN)

        serializer = TokenBookingSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        doctor = serializer.validated_data["doctor"]
        hospital = serializer.validated_data.get("hospital") or getattr(doctor, "hospital", None)
        if hospital is None:
            return Response({"detail": "Doctor has no hospital associated."}, status=status.HTTP_400_BAD_REQUEST)

        # Create token via your service helper (ensures numbering & constraints)
        token = create_token(patient=request.user, doctor=doctor, hospital=hospital, priority=0)

        # Estimate wait
        minutes, eta_dt = estimate_wait_for_token(doctor.id, token.token_number)

        # return data
        return Response({
            "token_id": token.id,
            "token_number": token.token_number,
            "estimated_wait_minutes": minutes,
            "eta": timezone.localtime(eta_dt).isoformat()
        }, status=status.HTTP_201_CREATED)


class WalkinTokenAPIView(APIView):
    """
    POST /api/token_queue/walkin/
    Body: { "doctor_id": <int>, "patient_name": "<name>" }
    Only users with receptionist role should be able to call this (IsReceptionist).
    """
    permission_classes = [IsReceptionist]

    def post(self, request, *args, **kwargs):
        serializer = WalkinTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        doctor_id = serializer.validated_data["doctor_id"]
        patient_name = serializer.validated_data["patient_name"].strip()

        # fetch doctor + hospital
        try:
            doctor = Doctor.objects.get(pk=doctor_id)
        except Doctor.DoesNotExist:
            return Response({"detail": "Doctor not found."}, status=status.HTTP_404_NOT_FOUND)

        hospital = getattr(doctor, "hospital", None)
        if hospital is None:
            return Response({"detail": "Doctor has no hospital associated."}, status=status.HTTP_400_BAD_REQUEST)

        # Create a pseudo patient user
        base_username = f"walkin_{timezone.now().strftime('%Y%m%d%H%M%S')}"
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1

        patient = User.objects.create_user(username=username)
        patient.first_name = patient_name
        patient.role = "patient"
        patient.set_unusable_password()
        # Optionally attach hospital to patient if your User model has hospital FK
        try:
            if hasattr(patient, "hospital") and hospital is not None:
                patient.hospital = hospital
        except Exception:
            pass
        patient.save()

        # create token via your service (ensures numbering & constraints)
        token = create_token(patient=patient, doctor=doctor, hospital=hospital, priority=0)

        # estimate wait
        minutes, eta_dt = estimate_wait_for_token(doctor.id, token.token_number)

        return Response({
            "token_id": token.id,
            "token_number": token.token_number,
            "patient_username": patient.username,
            "patient_name": patient_name,
            "estimated_wait_minutes": minutes,
            "eta": timezone.localtime(eta_dt).isoformat()
        }, status=status.HTTP_201_CREATED)
