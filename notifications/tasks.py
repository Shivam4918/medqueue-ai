from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, retry_kwargs={"max_retries": 3})
def send_token_alert(self, email, message):
    """
    Async email alert for token updates
    """
    if not email:
        return "No email provided"

    send_mail(
        subject="MedQueue Notification",
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )
    return "Email sent"


@shared_task(bind=True)
def send_turn_alert(self, phone, message):
    """
    Async SMS alert (mock / placeholder)
    """
    # 🔴 Replace with Twilio later
    print(f"[SMS MOCK] To: {phone} | Message: {message}")
    return "SMS sent"
