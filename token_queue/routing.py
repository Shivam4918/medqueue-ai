from django.urls import re_path
from .consumers import DoctorQueueConsumer

websocket_urlpatterns = [
    re_path(r"ws/queue/(?P<doctor_id>\d+)/$", DoctorQueueConsumer.as_asgi()),
]