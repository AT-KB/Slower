from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('process/<str:video_id>/', views.process_video, name='process_video'),
    path('process-multi/', views.process_multiple, name='process_multiple'),
    path('step/<str:video_id>/', views.show_process, name='show_process'),
    path('step/<str:video_id>/transcribe/', views.transcribe_step, name='transcribe_step'),
    path('step/<str:video_id>/summarize/', views.summarize_step, name='summarize_step'),
    path('step/<str:video_id>/script/', views.generate_script_step, name='generate_script_step'),
    path('step/<str:video_id>/synthesize/', views.synthesize_step, name='synthesize_step'),
    path('step/<str:video_id>/clear/', views.clear_process, name='clear_process'),
]
