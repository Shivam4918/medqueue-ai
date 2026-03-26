from pymongo import MongoClient, ASCENDING
from django.conf import settings


def get_mongo_client():
    mongo_url = getattr(settings, "MONGO_URL", None)
    if not mongo_url:
        return None
    try:
        return MongoClient(mongo_url)
    except Exception:
        return None


def get_analytics_db():
    client = get_mongo_client()
    if client:
        return client["medqueue_analytics"]
    return None


def get_events_collection():
    db = get_analytics_db()
    if db:
        return db["events"]
    return None


def ensure_indexes():
    collection = get_events_collection()
    if not collection:
        return

    collection.create_index(
        [("hospital_id", ASCENDING), ("timestamp", ASCENDING)],
        name="hospital_time_idx"
    )

    collection.create_index(
        [("doctor_id", ASCENDING), ("timestamp", ASCENDING)],
        name="doctor_time_idx"
    )

    collection.create_index(
        [("event", ASCENDING)],
        name="event_type_idx"
    )