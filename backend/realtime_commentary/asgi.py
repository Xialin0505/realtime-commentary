import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from llmserver.urls import websocket_urlpatterns

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "realtime_commentary.settings")

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter(websocket_urlpatterns),
})


