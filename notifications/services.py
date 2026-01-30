from users.models import User
from .tasks import send_token_alert, send_turn_alert


def notify_user_async(user: User, message: str):
    """
    Send email/SMS asynchronously via Celery
    """
    if not user:
        return

    # Email
    if user.email:
        send_token_alert.delay(user.email, message)

    # SMS (mock)
    if user.phone:
        send_turn_alert.delay(user.phone, message)
