from django.urls import path, re_path
from . import views

urlpatterns = [
    path('generate/', views.llmserver, name='llmserver'),
]

from llmserver.consumers import CommentaryConsumer

websocket_urlpatterns = [
    re_path(r'ws/commentary/(?P<video_id>[^/]+)/$$', CommentaryConsumer.as_asgi()),
]