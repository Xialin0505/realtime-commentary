from django.shortcuts import render

# Create your views here.
from rest_framework import generics
from .models import Video
from .serializers import VideoSerializer

class VideoListAPIView(generics.ListAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
