from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('process/<str:video_id>/', views.process_video, name='process_video'),
]
