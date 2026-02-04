# token_queue/views.py
from django.db import transaction
from django.utils import timezone

from rest_framework import viewsets, status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from users.permissions import IsReceptionist, IsDoctor
from users.models import User

from patients.models import Patient
from patients.services import get_or_create_patient_from_user

from doctors.models import Doctor
from hospitals.models import Hospital

from .models import Token
from .serializers import (
    TokenSerializer,
    TokenCreateSerializer,
    TokenBookingSerializer,
    WalkinTokenSerializer,
)
from .services import create_token, estimate_wait_for_token
from .realtime import broadcast_queue_update
from users.notifications import create_notification

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from django.core.paginator import Paginator
from django.db.models import Q
from django.utils.dateparse import parse_date
from notifications.services import notify_user_async

from analytics.events import *
# from analytics.events import (
#     log_event,
#     TOKEN_CREATED,
#     TOKEN_CALLED,
#     TOKEN_COMPLETED,
#     TOKEN_SKIPPED,
#     EMERGENCY_PRIORITY,
# )

# --------------------------------------------------
# Token CRUD (Admin / Receptionist / Doctor)
# --------------------------------------------------
class TokenViewSet(viewsets.ModelViewSet):
    queryset = Token.objects.all().order_by("-booked_at")
    serializer_class = TokenSerializer
    permission_classes = [IsReceptionist | IsDoctor]


# --------------------------------------------------
# Admin-style token creation (by patient_id or phone)
# --------------------------------------------------
class CreateTokenAPIView(APIView):
    permission_classes = []  # keep open if reception UI is unauthenticated

    def post(self, request):
        serializer = TokenCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        patient = data["patient"]          # already a Patient (serializer resolves)
        doctor = data["doctor"]
        hospital = data["hospital"]
        priority = data.get("priority", 0)

        token = create_token(
            patient=patient,
            doctor=doctor,
            hospital=hospital,
            priority=priority
        )

        broadcast_queue_update(
            doctor.id,
            {
                "event": "token_created",
                "token_id": token.id,
                "token_number": token.token_number,
                "status": token.status,
                "priority": token.priority
            }
        )

        minutes, eta_dt = estimate_wait_for_token(
            doctor.id,
            token.token_number
        )

        return Response({
            "token_id": token.id,
            "token_number": token.token_number,
            "status": token.status,
            "priority": token.priority,
            "estimated_wait_minutes": minutes,
            "eta": timezone.localtime(eta_dt).isoformat()
        }, status=status.HTTP_201_CREATED)


# --------------------------------------------------
# Patient online booking
# --------------------------------------------------
class TokenBookAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if getattr(request.user, "role", None) != "patient":
            return Response(
                {"detail": "Only patients may book tokens."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = TokenBookingSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        doctor = serializer.validated_data["doctor"]
        hospital = serializer.validated_data.get("hospital") or doctor.hospital

        # ✅ FIX: always resolve Patient from User
        patient = get_or_create_patient_from_user(request.user)

        token = create_token(
            patient=patient,
            doctor=doctor,
            hospital=hospital,
            priority=0
        )

        broadcast_queue_update(
            doctor.id,
            {
                "event": "token_created",
                "token_id": token.id,
                "token_number": token.token_number,
                "status": token.status,
                "priority": token.priority
            }
        )

        minutes, eta_dt = estimate_wait_for_token(
            doctor.id,
            token.token_number
        )

        return Response({
            "token_id": token.id,
            "token_number": token.token_number,
            "estimated_wait_minutes": minutes,
            "eta": timezone.localtime(eta_dt).isoformat()
        }, status=status.HTTP_201_CREATED)


# --------------------------------------------------
# Walk-in token creation (Receptionist)
# --------------------------------------------------
class WalkinTokenAPIView(APIView):
    permission_classes = [IsReceptionist]

    def post(self, request):
        serializer = WalkinTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        doctor_id = serializer.validated_data["doctor_id"]
        patient_name = serializer.validated_data["patient_name"].strip()

        try:
            doctor = Doctor.objects.get(pk=doctor_id)
        except Doctor.DoesNotExist:
            return Response(
                {"detail": "Doctor not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        hospital = doctor.hospital

        # Create temporary user for walk-in patient
        base_username = f"walkin_{timezone.now().strftime('%Y%m%d%H%M%S')}"
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1

        user = User.objects.create_user(
            username=username,
            role="patient"
        )
        user.first_name = patient_name
        user.set_unusable_password()
        user.save()

        # ✅ FIX: create Patient profile
        patient = Patient.objects.create(
            user=user,
            name=patient_name,
            phone=""
        )

        token = create_token(
            patient=patient,
            doctor=doctor,
            hospital=hospital,
            priority=0
        )

        broadcast_queue_update(
            doctor.id,
            {
                "event": "token_created",
                "token_id": token.id,
                "token_number": token.token_number,
                "status": token.status,
                "priority": token.priority
            }
        )


        minutes, eta_dt = estimate_wait_for_token(
            doctor.id,
            token.token_number
        )

        return Response({
            "token_id": token.id,
            "token_number": token.token_number,
            "patient_username": user.username,
            "patient_name": patient_name,
            "estimated_wait_minutes": minutes,
            "eta": timezone.localtime(eta_dt).isoformat()
        }, status=status.HTTP_201_CREATED)


# --------------------------------------------------
# Permissions helper
# --------------------------------------------------
def _user_can_manage_token(user, token: Token) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True

    role = getattr(user, "role", None)

    if role == "receptionist":
        return True

    if role == "doctor":
        return token.doctor.user_id == user.id

    return False


# --------------------------------------------------
# Doctor queue view
# --------------------------------------------------
class DoctorQueueAPIView(generics.ListAPIView):
    serializer_class = TokenSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        doctor_id = self.kwargs["doctor_id"]
        return Token.objects.filter(
            doctor_id=doctor_id,
            status__in=["waiting", "in_service"]
        ).order_by("-priority", "token_number")


# --------------------------------------------------
# Token actions
# --------------------------------------------------
class TokenActionBase(APIView):
    permission_classes = [IsAuthenticated]

    def get_token(self, pk):
        try:
            return Token.objects.get(pk=pk)
        except Token.DoesNotExist:
            return None

    def assert_manageable(self, user, token):
        if not _user_can_manage_token(user, token):
            return Response(
                {"detail": "Permission denied."},
                status=status.HTTP_403_FORBIDDEN
            )
        return None


class TokenCallAPIView(TokenActionBase):
    def post(self, request, pk):
        token = self.get_token(pk)
        if not token:
            return Response({"detail": "Not found."}, status=404)

        denied = self.assert_manageable(request.user, token)
        if denied:
            return denied

        with transaction.atomic():
            # 1️⃣ Mark current token as in service
            token.status = "in_service"
            token.called_at = timezone.now()
            token.save(update_fields=["status", "called_at", "updated_at"])
            
            log_event(
                event=TOKEN_CALLED,
                hospital_id=token.hospital.id,
                doctor_id=token.doctor.id,
                token_id=token.id,
            )

            # 2️⃣ Notify CURRENT patient (DB + async)
            if token.patient and token.patient.user:
                message = f"Your token {token.token_number} has been called. Please proceed."
                
                # In-app notification (DB)
                create_notification(token.patient.user, message)

                # Async SMS / Email (Celery)
                notify_user_async(token.patient.user, message)

            # 3️⃣ Find NEXT waiting token
            next_token = Token.objects.filter(
                doctor=token.doctor,
                status="waiting"
            ).order_by("token_number").first()

            # 4️⃣ Notify NEXT patient (DB + async)
            if next_token and next_token.patient and next_token.patient.user:
                message = f"Your token {next_token.token_number} is coming next."
                
                # In-app notification (DB)
                create_notification(next_token.patient.user, message)

                # Async SMS / Email (Celery)
                notify_user_async(next_token.patient.user, message)

        # 5️⃣ Real-time WebSocket broadcast
        broadcast_queue_update(
            token.doctor.id,
            {
                "event": "token_called",
                "token_id": token.id,
                "token_number": token.token_number,
                "status": "in_service"
            }
        )

        return Response({
            "detail": "Token called.",
            "token_number": token.token_number
        })

class TokenCompleteAPIView(TokenActionBase):
    def post(self, request, pk):
        token = self.get_token(pk)
        if not token:
            return Response({"detail": "Not found."}, status=404)

        denied = self.assert_manageable(request.user, token)
        if denied:
            return denied

        token.status = "completed"
        token.save(update_fields=["status", "updated_at"])

        log_event(
            event=TOKEN_COMPLETED,
            hospital_id=token.hospital.id,
            doctor_id=token.doctor.id,
            token_id=token.id,
        )

        # 🔴 REAL-TIME BROADCAST (ADD HERE)
        broadcast_queue_update(
            token.doctor.id,
            {
                "event": "token_completed",
                "token_id": token.id,
                "status": token.status
            }
        )
        

        return Response({"detail": "Token completed."})


class TokenSkipAPIView(TokenActionBase):
    def post(self, request, pk):
        token = self.get_token(pk)
        if not token:
            return Response({"detail": "Not found."}, status=404)

        denied = self.assert_manageable(request.user, token)
        if denied:
            return denied

        token.status = "skipped"
        token.save(update_fields=["status", "updated_at"])

        log_event(
            event=TOKEN_SKIPPED,
            hospital_id=token.hospital.id,
            doctor_id=token.doctor.id,
            token_id=token.id,
        )

        # 🔴 REAL-TIME BROADCAST (ADD HERE)
        broadcast_queue_update(
            token.doctor.id,
            {
                "event": "token_completed",  # skipped is also a completion
                "token_id": token.id,
                "status": token.status
            }
        )

        return Response({"detail": "Token skipped."})


class TokenPriorityAPIView(TokenActionBase):
    def post(self, request, pk):
        token = self.get_token(pk)
        if not token:
            return Response({"detail": "Not found."}, status=404)

        denied = self.assert_manageable(request.user, token)
        if denied:
            return denied

        try:
            priority = int(request.data.get("priority"))
            if priority not in (0, 1):
                raise ValueError
        except Exception:
            return Response(
                {"detail": "Invalid priority value."},
                status=status.HTTP_400_BAD_REQUEST
            )

        token.priority = priority
        token.save(update_fields=["priority", "updated_at"])

        log_event(
            event=EMERGENCY_PRIORITY,
            hospital_id=token.hospital.id,
            doctor_id=token.doctor.id,
            token_id=token.id,
            meta={"priority": token.priority},
        )

        # 🔴 REAL-TIME BROADCAST (ADD HERE)
        broadcast_queue_update(
            token.doctor.id,
            {
                "event": "token_priority_updated",
                "token_id": token.id,
                "priority": token.priority
            }
        )

        return Response({"detail": "Token priority updated.", "priority": priority})
    
class VerifyTokenAPIView(APIView):
    permission_classes = [IsAuthenticated, IsReceptionist]

    def get(self, request, token_id):
        try:
            token = Token.objects.get(id=token_id)
        except Token.DoesNotExist:
            return Response({"valid": False, "message": "Invalid token"}, status=404)

        if token.status in ["completed", "skipped"]:
            return Response({
                "valid": False,
                "message": "Token already used"
            })

        return Response({
            "valid": True,
            "token_id": token.id,
            "patient": token.patient.name,
            "doctor": token.doctor.name,
            "status": token.status
        })

class DoctorDelayAPIView(APIView):
    permission_classes = [IsAuthenticated, IsDoctor]

    def post(self, request, doctor_id):
        try:
            delay_minutes = int(request.data.get("delay_minutes", 0))
            reason = request.data.get("reason", "Not specified")
        except ValueError:
            return Response(
                {"detail": "Invalid delay minutes"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            doctor = Doctor.objects.get(id=doctor_id)
        except Doctor.DoesNotExist:
            return Response({"detail": "Doctor not found"}, status=404)

        # 🔵 ANALYTICS LOG
        log_event(
            event=DOCTOR_DELAY,
            hospital_id=doctor.hospital.id,
            doctor_id=doctor.id,
            meta={
                "delay_minutes": delay_minutes,
                "reason": reason,
            },
        )

        return Response({
            "detail": "Doctor delay logged",
            "delay_minutes": delay_minutes
        })

    
@login_required
def patient_dashboard(request):
    # Only patients allowed
    if getattr(request.user, "role", None) != "patient":
        return render(request, "patients/not_allowed.html")

    patient = get_or_create_patient_from_user(request.user)

    # Get active token
    token = Token.objects.filter(
        patient=patient,
        status__in=["waiting", "in_service"]
    ).select_related("doctor", "hospital").first()

    context = {
        "has_token": False
    }

    if token:
        minutes, eta_dt = estimate_wait_for_token(
            token.doctor.id,
            token.token_number
        )

        context.update({
            "has_token": True,
            "token_number": token.token_number,
            "doctor_name": token.doctor.name,
            "hospital_name": token.hospital.name,
            "status": token.status.replace("_", " ").title(),
            "estimated_wait": minutes,
            "eta": timezone.localtime(eta_dt),
        })

    return render(request, "patients/home.html", context)

@login_required
def patient_token_history(request):
    # Only patients allowed
    if getattr(request.user, "role", None) != "patient":
        return render(request, "patients/not_allowed.html")

    patient = get_or_create_patient_from_user(request.user)

    tokens = Token.objects.filter(
        patient=patient,
        status__in=["completed", "skipped"]
    ).select_related("doctor").order_by("-created_at")

    # Optional date filter
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if start_date:
        tokens = tokens.filter(created_at__date__gte=parse_date(start_date))
    if end_date:
        tokens = tokens.filter(created_at__date__lte=parse_date(end_date))

    # Pagination (10 per page)
    paginator = Paginator(tokens, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "start_date": start_date or "",
        "end_date": end_date or "",
    }

    return render(request, "patients/history.html", context)