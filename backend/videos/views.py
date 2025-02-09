from django.shortcuts import render

# Create your views here.
from rest_framework import generics
from .models import Video
from .serializers import VideoSerializer
from .models import Screenshot
from .serializers import ScreenshotSerializer

class ScreenshotUploadAPIView(generics.CreateAPIView):
    queryset = Screenshot.objects.all()
    serializer_class = ScreenshotSerializer

class VideoListAPIView(generics.ListAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
