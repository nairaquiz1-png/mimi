from django.urls import path
from .consumers import JobConsumer

websocket_urlpatterns = [
    path("ws/job/<int:job_id>/", JobConsumer.as_asgi()),
]