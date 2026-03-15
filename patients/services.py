from .models import Patient
from users.models import Notification
from token_queue.models import Token
from django.utils import timezone

def get_or_create_patient_from_user(user):
    patient, _ = Patient.objects.get_or_create(
        user=user,
        defaults={
            "name": user.get_full_name() or user.username,
            "phone": user.phone or ""
        }
    )
    return patient

def check_and_notify_queue(token):

    """
    Send smart notifications to patient based on queue status
    """

    doctor = token.doctor

    # Get active queue
    queue = Token.objects.filter(
        doctor=doctor,
        status__in=["waiting", "in_service"],
        booked_at__date=timezone.localdate()
    ).order_by("token_number")

    tokens = list(queue)

    for index, t in enumerate(tokens):

        position = index + 1

        # Notify when token is about to be called
        if position == 3 and t.patient.user:

            Notification.objects.create(
                user=t.patient.user,
                message=f"Your token A-{t.token_number} will be called soon. Please be ready."
            )

        # Notify when next
        if position == 2 and t.patient.user:

            Notification.objects.create(
                user=t.patient.user,
                message=f"Your turn is almost here. Token A-{t.token_number} is next."
            )

        # Notify when now serving
        if position == 1 and t.status == "waiting":

            Notification.objects.create(
                user=t.patient.user,
                message=f"Please proceed to consultation. Token A-{t.token_number} is being called."
            )