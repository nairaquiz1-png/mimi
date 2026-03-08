from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def broadcast_job_location(job_id, lat, lng, status):
    """
    Broadcast job location updates to all connected WebSocket clients.
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"job_{job_id}",
        {
            "type": "job_update",  # matches JobConsumer.job_update
            "data": {
                "lat": lat,
                "lng": lng,
                "status": status,
            },
        }
    )