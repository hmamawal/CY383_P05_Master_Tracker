from django.urls import path
from . import views

urlpatterns = [
    # Original challenge-related paths
    path("", views.home, name="home"),
    path("add_challenge/", views.add_challenge, name='add_challenge'),
    path('challenge/<int:challenge_id>/', views.challenge_detail, name='challenge_detail'),
    
    # New task management paths
    path('tasks/', views.task_dashboard, name='task_dashboard'),
    path('tasks/create/', views.create_task, name='create_task'),
    path('tasks/<int:task_id>/', views.task_detail, name='task_detail'),
    path('notifications/read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('tasks/generate-ncors/', views.generate_ncors, name='generate_ncors'),
]
