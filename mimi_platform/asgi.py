import os
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
import platform_api.routing  # your app routing for WebSockets

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mimi_platform.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            platform_api.routing.websocket_urlpatterns
        )
    ),
})