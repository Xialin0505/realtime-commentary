from django.urls import path
from .views import VideoListAPIView

urlpatterns = [
    path('api/videos/', VideoListAPIView.as_view(), name='video_list_api'),
]
