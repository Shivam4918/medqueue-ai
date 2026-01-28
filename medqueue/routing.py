# from django.urls import re_path

# # import consumers here when you create them
# # from api import consumers

# websocket_urlpatterns = [
#     # Example placeholder (no consumer yet)
#     # re_path(r'ws/queue/(?P<doctor_id>\d+)/$', consumers.QueueConsumer.as_asgi()),
# ]

from django.urls import re_path
from token_queue.consumers import DoctorQueueConsumer

websocket_urlpatterns = [
    re_path(r"ws/queue/doctor/(?P<doctor_id>\d+)/$", DoctorQueueConsumer.as_asgi()),
]

