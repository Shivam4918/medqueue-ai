import importlib
import token_queue.services as tq_services
importlib.reload(tq_services)
from datetime import timedelta
from typing import Tuple
from django.utils import timezone
from django.db.models import Max
from patients.models import Patient
# imports adjusted for your app names
from token_queue.models import Token       # <- token model lives in token_queue
from doctors.models import Doctor
from hospitals.models import Hospital
from users.models import User


def _today_date():
    return timezone.localtime(timezone.now()).date()


def generate_next_token_number(doctor_id: int) -> int:
    today = _today_date()

    if hasattr(Token, "booked_date"):
        qs = Token.objects.filter(doctor_id=doctor_id, booked_date=today)
    else:
        qs = Token.objects.filter(doctor_id=doctor_id, booked_at__date=today)

    max_val = qs.aggregate(max_token=Max("token_number"))["max_token"]
    if max_val is None:
        return 1
    return int(max_val) + 1


def estimate_wait_for_token(doctor_id: int, token_number: int, avg_minutes_per_patient: int = 8) -> Tuple[int, timezone.datetime]:
    today = _today_date()
    pending_statuses = ["waiting", "in_service"]

    if hasattr(Token, "booked_date"):
        qs = Token.objects.filter(
            doctor_id=doctor_id,
            booked_date=today,
            status__in=pending_statuses,
            token_number__lt=token_number
        )
    else:
        qs = Token.objects.filter(
            doctor_id=doctor_id,
            booked_at__date=today,
            status__in=pending_statuses,
            token_number__lt=token_number
        )

    position = qs.count()
    eta_minutes = position * int(avg_minutes_per_patient)
    eta_datetime = timezone.now() + timedelta(minutes=eta_minutes)
    return eta_minutes, eta_datetime


def create_token(patient: Patient, doctor: Doctor, hospital: Hospital = None, priority: int = 0) -> Token:
    if hospital is None:
        hospital = getattr(doctor, "hospital", None)
        if hospital is None:
            raise ValueError("Hospital must be provided either explicitly or via doctor.hospital")

    next_number = generate_next_token_number(doctor.id)
    now = timezone.now()
    kwargs = {
        "hospital": hospital,
        "doctor": doctor,
        "patient": patient,
        "token_number": next_number,
        "booked_at": now,
        "priority": priority,
    }
    if hasattr(Token, "booked_date"):
        kwargs["booked_date"] = _today_date()

    token = Token.objects.create(**kwargs)
    return token
