# analytics/cleanup.py
from datetime import datetime, timedelta
from .mongo_client import events_collection

RETENTION_DAYS = 90


def cleanup_old_events():
    cutoff = datetime.utcnow() - timedelta(days=RETENTION_DAYS)

    result = events_collection.delete_many({
        "timestamp": {"$lt": cutoff}
    })

    return result.deleted_count
