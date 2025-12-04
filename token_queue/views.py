# token_queue/views.py
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, status, generics
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


# -----------------------------
# Added: doctor queue + token actions
# -----------------------------
def _user_can_manage_token(user, token: Token) -> bool:
    """Return True if user may manage this token."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    role = getattr(user, "role", None)
    if role == "receptionist":
        # receptionist may manage tokens (you could restrict by hospital if user.hospital exists)
        return True
    if role == "doctor":
        # doctor may manage their own tokens only
        try:
            return token.doctor.user_id == user.id
        except Exception:
            return getattr(token.doctor, "user_id", None) == user.id
    return False


class DoctorQueueAPIView(generics.ListAPIView):
    """
    GET /api/doctors/<id>/queue/
    List active tokens for a doctor (waiting + in_service)
    """
    serializer_class = TokenSerializer
    permission_classes = [IsAuthenticated]  # change if you want stricter checks

    def get_queryset(self):
        doctor_id = self.kwargs.get("doctor_id")
        return Token.objects.filter(
            doctor_id=doctor_id,
            status__in=["waiting", "in_service"]
        ).order_by("-priority", "token_number")  # priority desc then number asc


class TokenActionBase(APIView):
    permission_classes = [IsAuthenticated]

    def get_token(self, pk):
        try:
            return Token.objects.get(pk=pk)
        except Token.DoesNotExist:
            return None

    def assert_manageable(self, request_user, token):
        if not _user_can_manage_token(request_user, token):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        return None


class TokenCallAPIView(TokenActionBase):
    """
    POST /api/tokens/<id>/call/
    Mark token as in_service and set called_at to now.
    """
    def post(self, request, pk, *args, **kwargs):
        token = self.get_token(pk)
        if not token:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        denied = self.assert_manageable(request.user, token)
        if denied:
            return denied

        with transaction.atomic():
            token.status = "in_service"
            token.called_at = timezone.now()
            token.save(update_fields=["status", "called_at", "updated_at"])

        return Response({
            "detail": "Token called.",
            "token_id": token.id,
            "token_number": token.token_number,
            "status": token.status,
            "called_at": token.called_at
        })


class TokenCompleteAPIView(TokenActionBase):
    """
    POST /api/tokens/<id>/complete/
    Mark token as completed.
    """
    def post(self, request, pk, *args, **kwargs):
        token = self.get_token(pk)
        if not token:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        denied = self.assert_manageable(request.user, token)
        if denied:
            return denied

        with transaction.atomic():
            token.status = "completed"
            token.save(update_fields=["status", "updated_at"])

        return Response({"detail": "Token completed.", "token_id": token.id, "status": token.status})


class TokenSkipAPIView(TokenActionBase):
    """
    POST /api/tokens/<id>/skip/
    Mark token as skipped.
    """
    def post(self, request, pk, *args, **kwargs):
        token = self.get_token(pk)
        if not token:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        denied = self.assert_manageable(request.user, token)
        if denied:
            return denied

        with transaction.atomic():
            token.status = "skipped"
            token.save(update_fields=["status", "updated_at"])

        return Response({"detail": "Token skipped.", "token_id": token.id, "status": token.status})


class TokenPriorityAPIView(TokenActionBase):
    """
    POST /api/tokens/<id>/priority/
    Body: {"priority": 0|1}
    Set or update priority for a token.
    """
    def post(self, request, pk, *args, **kwargs):
        token = self.get_token(pk)
        if not token:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        denied = self.assert_manageable(request.user, token)
        if denied:
            return denied

        priority = request.data.get("priority")
        try:
            priority = int(priority)
            if priority not in (0, 1):
                raise ValueError()
        except Exception:
            return Response({"detail": "Invalid priority value. Use 0 or 1."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            token.priority = priority
            token.save(update_fields=["priority", "updated_at"])

        return Response({
            "detail": "Token priority updated.",
            "token_id": token.id,
            "token_number": token.token_number,
            "priority": token.priority
        })
