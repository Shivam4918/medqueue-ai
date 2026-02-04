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
DOCTOR_DELAY = "doctor_delay"
EMERGENCY_PRIORITY = "emergency_priority"


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
    collection = get_events_collection()

    document = {
        "event": event,
        "hospital_id": hospital_id,
        "doctor_id": doctor_id,
        "token_id": token_id,
        "timestamp": datetime.utcnow(),
        "meta": meta or {},
    }

    collection.insert_one(document)
