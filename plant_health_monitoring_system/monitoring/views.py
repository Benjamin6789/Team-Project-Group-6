# monitoring/views.py
from django.shortcuts import render
from .models import PlantData

def dashboard(request):
    # Get the latest 10 records
    plant_data = PlantData.objects.all().order_by('-timestamp')[:10]
    return render(request, 'monitoring/dashboard.html', {'plant_data': plant_data})
def welcome(request):
    return render(request, 'monitoring/welcome.html')