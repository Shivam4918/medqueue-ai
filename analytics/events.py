from datetime import datetime
from typing import Optional, Dict

from .mongo_client import get_events_collection


# -------------------------
# Event Types (Constants)
# -------------------------
TOKEN_CREATED = "token_created"
TOKEN_CALLED = "token_called"
TOKEN_COMPLETED = "token_completed"
TOKEN_SKIPPED = "token_skipped"
EMERGENCY_PRIORITY = "emergency_priority"
DOCTOR_DELAY = "doctor_delay"

ALLOWED_EVENTS = {
    TOKEN_CREATED,
    TOKEN_CALLED,
    TOKEN_COMPLETED,
    TOKEN_SKIPPED,
    EMERGENCY_PRIORITY,
    DOCTOR_DELAY,
}


def log_event(
    event: str,
    hospital_id: int,
    doctor_id: Optional[int] = None,
    token_id: Optional[int] = None,
    meta: Optional[Dict] = None,
):
    """
    Central analytics event logger
    """

    # -------------------------
    # Validation
    # -------------------------
    if event not in ALLOWED_EVENTS:
        raise ValueError(f"Invalid event type: {event}")

    if not hospital_id:
        raise ValueError("hospital_id is required")

    # -------------------------
    # MongoDB Collection
    # -------------------------
    collection = get_events_collection()

    # -------------------------
    # Event Document
    # -------------------------
    document = {
        "event": event,
        "hospital_id": int(hospital_id),
        "doctor_id": int(doctor_id) if doctor_id else None,
        "token_id": int(token_id) if token_id else None,
        "timestamp": datetime.utcnow(),
        "meta": meta or {},
    }

    collection.insert_one(document)
