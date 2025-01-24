from django.urls import re_path
from llmserver.consumers import CommentaryConsumer

websocket_urlpatterns = [
    re_path(r'ws/commentary/$', CommentaryConsumer.as_asgi()),
]