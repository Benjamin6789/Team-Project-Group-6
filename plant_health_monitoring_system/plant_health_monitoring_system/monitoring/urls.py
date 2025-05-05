# monitoring/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.welcome, name='welcome'),  # Add this to map the URL to the welcome view
    path('dashboard/', views.dashboard, name='dashboard'),
    path('api/latest-data/', views.get_latest_data, name='get_latest_data'),
    path('api/data-by-range/', views.get_data_by_time_range, name='get_data_by_time_range'),
    path('api/update-interval/', views.update_collection_interval, name='update_collection_interval'),
    path('api/system-status/', views.get_system_status, name='get_system_status'),
]
