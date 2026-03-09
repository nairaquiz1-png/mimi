import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import JobLocationLog

class JobConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.job_id = self.scope['url_route']['kwargs']['job_id']
        self.group_name = f"job_{self.job_id}"

        # Join the job group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        print(f"WebSocket connected for job {self.job_id}")

    async def disconnect(self, close_code):
        # Leave the group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        print(f"WebSocket disconnected for job {self.job_id}")

    async def receive(self, text_data):
        """
        Receive a message from the WebSocket.
        Expected format from provider:
        {
            "lat": 6.5244,
            "lng": 3.3792,
            "status": "in_progress"
        }
        """
        data = json.loads(text_data)
        lat = data.get("lat")
        lng = data.get("lng")
        status = data.get("status", "in_progress")

        user = self.scope["user"]
        # Save provider location to database if authenticated
        if user.is_authenticated and user.role == "provider" and lat is not None and lng is not None:
            await sync_to_async(JobLocationLog.objects.create)(
                job_id=self.job_id,
                provider=user,
                lat=lat,
                lng=lng,
            )

        # Broadcast the location update to the group
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "job_update",  # matches the handler below
                "data": {
                    "lat": lat,
                    "lng": lng,
                    "status": status
                }
            }
        )

    async def job_update(self, event):
        """
        Send location updates to all clients in the group.
        Frontend receives: { lat, lng, status }
        """
        await self.send(text_data=json.dumps(event["data"]))