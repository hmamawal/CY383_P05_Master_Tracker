from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("add_challenge/", views.add_challenge, name='add_challenge'),
    path('challenge/<int:challenge_id>/', views.challenge_detail, name='challenge_detail'),
]
