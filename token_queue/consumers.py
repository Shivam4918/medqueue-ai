import json
from channels.generic.websocket import AsyncWebsocketConsumer

class DoctorQueueConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.doctor_id = self.scope["url_route"]["kwargs"]["doctor_id"]
        self.room_group_name = f"doctor_{self.doctor_id}"

        # Join doctor-specific room
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """
        We are not receiving messages from client.
        This consumer is PUSH-only.
        """
        pass

    async def queue_update(self, event):
        """
        Called when server sends queue updates
        """
        await self.send(text_data=json.dumps(event["data"]))
