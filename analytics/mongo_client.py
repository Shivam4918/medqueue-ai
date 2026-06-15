# analytics/mongo_client.py

from pymongo import MongoClient, ASCENDING
from django.conf import settings


def get_mongo_url():
    """
    Safe getter for Mongo URL
    """
    return getattr(settings, "MONGO_URL", "mongodb://localhost:27017")


def get_mongo_client():
    return MongoClient(get_mongo_url(), serverSelectionTimeoutMS=2000)


def get_analytics_db():
    client = get_mongo_client()
    return client["medqueue_analytics"]


def get_events_collection():
    db = get_analytics_db()
    return db["events"]


def ensure_indexes():
    try:
        db = get_analytics_db()
        events_collection = db["events"]

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

        print("MongoDB indexes ensured")

    except Exception as e:
        print("MongoDB not ready:", e)