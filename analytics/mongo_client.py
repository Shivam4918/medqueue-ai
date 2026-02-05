from pymongo import MongoClient, ASCENDING
from django.conf import settings


client = MongoClient(settings.MONGO_URL)
db = client["medqueue_analytics"]
events_collection = db["events"]

def get_mongo_client():
    """
    Returns a MongoDB client instance
    """
    return MongoClient(settings.MONGO_URL)


def get_analytics_db():
    """
    Analytics database
    """
    client = get_mongo_client()
    return client["medqueue_analytics"]


def get_events_collection():
    """
    Centralized events collection
    """
    db = get_analytics_db()
    return db["events"]

def ensure_indexes():
    """
    Create indexes for fast analytics queries.
    Safe to call multiple times.
    """
    events_collection.create_index(
        [("hospital_id", ASCENDING), ("timestamp", ASCENDING)],
        name="hospital_time_idx"
    )

    events_collection.create_index(
        [("doctor_id", ASCENDING), ("timestamp", ASCENDING)],
        name="doctor_time_idx"
    )

    events_collection.create_index(
        [("event", ASCENDING)],
        name="event_type_idx"
    )

