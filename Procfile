web: python manage.py migrate && daphne -b 0.0.0.0 -p $PORT medqueue.asgi:application
worker: celery -A medqueue worker --loglevel=info
beat: celery -A medqueue beat --loglevel=info