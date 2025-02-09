from django.urls import path
from .views import upload_screenshot

urlpatterns = [
    path('api/upload_screenshot/', upload_screenshot, name='upload_screenshot'),
]
