from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'analytics'

    def ready(self):
        try:
            from .mongo_client import ensure_indexes
            ensure_indexes()
        except Exception as e:
            print("MongoDB not ready, skipping index creation:", e)