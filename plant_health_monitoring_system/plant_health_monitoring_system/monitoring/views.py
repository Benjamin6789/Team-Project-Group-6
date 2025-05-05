# monitoring/views.py
from django.shortcuts import render
from .models import PlantData, SystemStatus
from django.http import JsonResponse
from django.conf import settings  # Import Django settings
import json
import os
import sys
import importlib.util
import logging
from datetime import datetime, timedelta
from django.utils import timezone

# Set up logging
logger = logging.getLogger(__name__)

def dashboard(request):
    # Get the latest 10 records
    plant_data = PlantData.objects.all().order_by('-timestamp')[:10]
    # Get the current system status
    system_status = SystemStatus.get_current_status()
    
    # Set auto_start flag to true so JavaScript knows to start monitoring
    return render(request, 'monitoring/dashboard.html', {
        'plant_data': plant_data,
        'auto_start': True,
        'system_status': system_status
    })

def welcome(request):
    return render(request, 'monitoring/welcome.html')

def get_latest_data(request):
    # Get the latest 10 records
    plant_data = PlantData.objects.all().order_by('-timestamp')[:10]
    data = [{
        'timestamp': entry.timestamp.isoformat(),
        'temperature': entry.temperature,
        'humidity': entry.humidity,
        'soil_moisture': entry.soil_moisture,
        'air_quality': entry.air_quality,
        'light': entry.light if entry.light is not None else 0,
        'pressure': entry.pressure if entry.pressure is not None else 0,
        'oxidising': entry.oxidising if entry.oxidising is not None else 0,
        'reducing': entry.reducing if entry.reducing is not None else 0
    } for entry in plant_data]
    # Reverse data to show oldest first for consistent timeline display
    data.reverse()
    return JsonResponse(data, safe=False)

def get_system_status(request):
    """Get the current system status information"""
    status = SystemStatus.get_current_status()
    
    # Format the data for JSON response
    status_data = {
        'timestamp': status.timestamp.isoformat() if status.timestamp else None,
        'last_collection_time': status.last_collection_time.isoformat() if status.last_collection_time else None,
        'collection_duration': status.collection_duration,
        'is_collecting_delayed': status.is_collecting_delayed,
        'status_message': status.status_message
    }
    
    return JsonResponse(status_data)

def get_data_by_time_range(request):
    """Fetch data for a specific time range (60s, 1h, 24h)"""
    time_range = request.GET.get('range', '60s')
    logger.info(f"Fetching data for time range: {time_range}")
    
    now = timezone.now()
    
    # Calculate time range
    if time_range == '60s':
        start_time = now - timedelta(seconds=60)
        # Limit to 20 points max for 60s view to avoid overwhelming the charts
        limit = 20
    elif time_range == '1h':
        start_time = now - timedelta(hours=1)
        # For 1h, get one point per 3 minutes (20 points total)
        limit = 20
    elif time_range == '24h':
        start_time = now - timedelta(days=1)
        # For 24h, get one point per hour (24 points total)
        limit = 24
    else:
        # Default to 60 seconds
        start_time = now - timedelta(seconds=60)
        limit = 20
    
    # Query the database for data in the specified range
    if time_range == '60s':
        # For short ranges, get all points
        plant_data = PlantData.objects.filter(timestamp__gte=start_time).order_by('-timestamp')[:limit]
    else:
        # For longer ranges, we can't get every data point (would be too many),
        # so instead we get a sampling by taking the latest points up to our limit
        plant_data = PlantData.objects.filter(timestamp__gte=start_time).order_by('-timestamp')
        
        # Simple sampling approach - get evenly spaced points
        total_points = plant_data.count()
        if total_points > limit:
            # Get a subset of points that are roughly evenly spaced
            sample_ids = []
            step = total_points // limit
            for i in range(0, total_points, step):
                if len(sample_ids) < limit:
                    sample_ids.append(i)
            
            # Get the sampled points by their indices
            sampled_data = []
            all_data = list(plant_data)
            for idx in sample_ids:
                if idx < len(all_data):
                    sampled_data.append(all_data[idx])
            plant_data = sampled_data
    
    # Format the data for JSON response
    data = [{
        'timestamp': entry.timestamp.isoformat(),
        'temperature': entry.temperature,
        'humidity': entry.humidity,
        'soil_moisture': entry.soil_moisture,
        'air_quality': entry.air_quality,
        'light': entry.light if entry.light is not None else 0,
        'pressure': entry.pressure if entry.pressure is not None else 0,
        'oxidising': entry.oxidising if entry.oxidising is not None else 0,
        'reducing': entry.reducing if entry.reducing is not None else 0
    } for entry in plant_data]
    
    # Ensure data is in chronological order (oldest first) for time series display
    data.reverse()
    
    return JsonResponse(data, safe=False)

def update_collection_interval(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_interval = float(data.get('interval', 5.0))
            
            # Validate the interval (minimum 0.5 second, maximum 10 seconds)
            if new_interval < 0.5:
                new_interval = 0.5
            elif new_interval > 10.0:
                new_interval = 10.0
            
            logger.info(f"Received request to update collection interval to {new_interval} seconds")
            
            # Construct the absolute path to the update file using BASE_DIR
            update_file_path = os.path.join(settings.BASE_DIR, 'Get-Data', 'interval_update.txt')
            logger.info(f"Writing interval update to: {update_file_path}")

            # Write to the file that the collector checks for updates
            try:
                with open(update_file_path, 'w') as f:
                    f.write(str(new_interval))
                logger.info(f"Successfully wrote interval {new_interval} to {update_file_path}")
            except IOError as e:
                logger.error(f"Failed to write to interval update file {update_file_path}: {str(e)}")
                return JsonResponse({'success': False, 'error': f'Server error writing update file: {str(e)}'}, status=500)
            
            return JsonResponse({'success': True, 'new_interval': new_interval})
        except Exception as e:
            logger.error(f"Error processing interval update request: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    else:
        return JsonResponse({'success': False, 'error': 'Only POST method is allowed'}, status=405)