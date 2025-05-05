# plant_health_monitoring_system/urls.py

from django.contrib import admin
from django.urls import path, include  # Make sure include is imported here

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('monitoring.urls')),  # This line includes the URLs from the monitoring app
]
