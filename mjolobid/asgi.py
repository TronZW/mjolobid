"""
ASGI config for mjolobid project.
"""

import os
import django

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mjolobid.settings')

# Configure Django
django.setup()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

# Import WebSocket URL patterns after Django is configured
from notifications.routing import websocket_urlpatterns as notification_websocket_urlpatterns
from messaging.routing import websocket_urlpatterns as messaging_websocket_urlpatterns

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
