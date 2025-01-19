from django.urls import path
from . import views

urlpatterns = [
    path('llmserver/', views.llmserver, name='llmserver'),
]