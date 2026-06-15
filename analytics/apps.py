from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'analytics'

    def ready(self):
        import threading
        def run_indexing():
            try:
                from .mongo_client import ensure_indexes
                ensure_indexes()
            except Exception as e:
                print("MongoDB index creation background task failed:", e)
        threading.Thread(target=run_indexing, daemon=True).start()