from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


def broadcast_queue_update(doctor_id, data):
    
    print("Broadcasting queue update:", doctor_id, data)
    channel_layer = get_channel_layer()

    group_name = f"doctor_{doctor_id}"

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "queue_update",
            "data": data
        }
    )