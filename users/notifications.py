from .models import Notification, User

def create_notification(user: User, message: str):
    if not user:
        return
    Notification.objects.create(
        user=user,
        message=message
    )
