from datetime import datetime, timedelta
from django.utils import timezone

from .mongo_client import get_events_collection
from .events import (
    TOKEN_CREATED,
    TOKEN_CALLED,
    TOKEN_COMPLETED,
    TOKEN_SKIPPED,
)

def _today_range():
    now = timezone.now()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return start, end

def total_patients_today(hospital_id: int) -> int:
    collection = get_events_collection()
    start, end = _today_range()

    pipeline = [
        {
            "$match": {
                "event": TOKEN_CREATED,
                "hospital_id": hospital_id,
                "timestamp": {"$gte": start, "$lt": end},
            }
        },
        {"$count": "total"},
    ]

    result = list(collection.aggregate(pipeline))
    return result[0]["total"] if result else 0

def tokens_per_doctor(hospital_id: int):
    collection = get_events_collection()
    start, end = _today_range()

    pipeline = [
        {
            "$match": {
                "event": TOKEN_CREATED,
                "hospital_id": hospital_id,
                "timestamp": {"$gte": start, "$lt": end},
            }
        },
        {
            "$group": {
                "_id": "$doctor_id",
                "total_tokens": {"$sum": 1},
            }
        },
        {"$sort": {"total_tokens": -1}},
    ]

    return list(collection.aggregate(pipeline))

def peak_opd_hours(hospital_id: int):
    collection = get_events_collection()
    start, end = _today_range()

    pipeline = [
        {
            "$match": {
                "event": TOKEN_CREATED,
                "hospital_id": hospital_id,
                "timestamp": {"$gte": start, "$lt": end},
            }
        },
        {
            "$group": {
                "_id": {"$hour": "$timestamp"},
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"count": -1}},
    ]

    return list(collection.aggregate(pipeline))

def average_wait_time_minutes(hospital_id: int) -> float:
    collection = get_events_collection()
    start, end = _today_range()

    pipeline = [
        {
            "$match": {
                "event": {"$in": [TOKEN_CREATED, TOKEN_CALLED]},
                "hospital_id": hospital_id,
                "timestamp": {"$gte": start, "$lt": end},
            }
        },
        {
            "$group": {
                "_id": "$token_id",
                "created_at": {
                    "$min": {
                        "$cond": [
                            {"$eq": ["$event", TOKEN_CREATED]},
                            "$timestamp",
                            None,
                        ]
                    }
                },
                "called_at": {
                    "$max": {
                        "$cond": [
                            {"$eq": ["$event", TOKEN_CALLED]},
                            "$timestamp",
                            None,
                        ]
                    }
                },
            }
        },
        {
            "$project": {
                "wait_minutes": {
                    "$divide": [
                        {"$subtract": ["$called_at", "$created_at"]},
                        1000 * 60,
                    ]
                }
            }
        },
        {
            "$group": {
                "_id": None,
                "avg_wait": {"$avg": "$wait_minutes"},
            }
        },
    ]

    result = list(collection.aggregate(pipeline))
    # return round(result[0]["avg_wait"], 2) if result else 0.0
    if not result:
        return 0.0

    avg = result[0].get("avg_wait")

    if avg is None:
        return 0.0

    return round(avg, 2)


def no_show_rate(hospital_id: int) -> float:
    collection = get_events_collection()
    start, end = _today_range()

    total = collection.count_documents({
        "event": TOKEN_CREATED,
        "hospital_id": hospital_id,
        "timestamp": {"$gte": start, "$lt": end},
    })

    skipped = collection.count_documents({
        "event": TOKEN_SKIPPED,
        "hospital_id": hospital_id,
        "timestamp": {"$gte": start, "$lt": end},
    })

    if total == 0:
        return 0.0

    return round((skipped / total) * 100, 2)
