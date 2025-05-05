# monitoring/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.welcome, name='welcome'),  # Add this to map the URL to the welcome view
path('dashboard/', views.dashboard, name='dashboard'),
]
