from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

def broadcast_queue_update(doctor_id: int, data: dict):
    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        f"doctor_{doctor_id}",
        {
            "type": "queue_update",
            "data": data
        }
    )
