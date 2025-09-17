"""
ASGI config for mjolobid project.
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from notifications.routing import websocket_urlpatterns as notification_websocket_urlpatterns
from messaging.routing import websocket_urlpatterns as messaging_websocket_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mjolobid.settings')

# Combine all WebSocket URL patterns
all_websocket_urlpatterns = notification_websocket_urlpatterns + messaging_websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            all_websocket_urlpatterns
        )
    ),
})
