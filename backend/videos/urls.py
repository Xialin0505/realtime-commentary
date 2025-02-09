from django.urls import path
from .views import VideoListAPIView
from .views import ScreenshotUploadAPIView

urlpatterns = [
    path('api/videos/', VideoListAPIView.as_view(), name='video_list_api'),
    path('api/upload_screenshot/', ScreenshotUploadAPIView.as_view(), name='upload_screenshot'),
]
