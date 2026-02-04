from pymongo import MongoClient
from django.conf import settings


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
