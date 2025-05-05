#!/usr/bin/env python3
# collector.py - Continuously collects data from SEES sensors and saves to CSV

from SEES import Sensors
from datetime import datetime
import time
import csv
import os
import sys
import signal
import django
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("collector.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("sensor_collector")

# Setup Django environment to save data to the database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plant_health_monitoring_system.settings')
django.setup()

# Import Django models after setting up Django environment
from monitoring.models import PlantData, SystemStatus
from django.utils import timezone

# Global variables for graceful shutdown and collection interval
running = True
data_collection_interval = 5.0  # time in seconds
INTERVAL_UPDATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "interval_update.txt")

def signal_handler(sig, frame):
    """Handle Ctrl+C for graceful shutdown"""
    global running
    logger.info("Shutdown signal received. Exiting gracefully...")
    running = False

# Register the signal handler
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def check_for_interval_update():
    """Check if there's a new interval update requested"""
    global data_collection_interval
    if os.path.exists(INTERVAL_UPDATE_FILE):
        try:
            with open(INTERVAL_UPDATE_FILE, 'r') as f:
                new_interval = float(f.read().strip())
                if 0.5 <= new_interval <= 10.0:
                    if new_interval != data_collection_interval:
                        logger.info(f"Updating collection interval from {data_collection_interval} to {new_interval} seconds")
                        data_collection_interval = new_interval
            # Remove the file after reading it
            os.remove(INTERVAL_UPDATE_FILE)
        except Exception as e:
            logger.error(f"Error reading interval update: {str(e)}")

def update_system_status(collection_duration):
    """Update the system status with the latest collection information"""
    try:
        status = SystemStatus.get_current_status()
        status.last_collection_time = timezone.now()
        status.collection_duration = collection_duration
        
        # Check if collection time exceeds the interval
        if collection_duration > data_collection_interval:
            status.is_collecting_delayed = True
            status.status_message = f"Warning: Data collection taking longer ({collection_duration:.2f}s) than the set interval ({data_collection_interval:.2f}s)"
            logger.warning(status.status_message)
        else:
            status.is_collecting_delayed = False
            status.status_message = "Data collection running normally"
        
        status.save()
    except Exception as e:
        logger.error(f"Error updating system status: {str(e)}")

def main():
    """Main data collection loop"""
    sensors = Sensors()
    
    # CSV file setup
    fields = ["Time", "Soil Moisture", "Temperature", "Nh3", "Humidity", "Pressure", "Light", "Oxidizing", "Reducing"]
    global data_collection_interval
    
    file_name = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Data.csv")
    
    # Create the CSV file if it doesn't exist
    if not os.path.isfile(file_name):
        with open(file_name, "w") as f:
            writer = csv.writer(f)
            writer.writerow(fields)
    
    logger.info(f"Starting data collection. Writing to {file_name}")
    logger.info(f"Collection interval: {data_collection_interval} seconds")
    
    # Main collection loop
    cache = []
    cache_size = 15 # Flush to CSV every 5 readings
    last_check_time = time.time()
    check_interval = 2.0  # Check for interval updates every 2 seconds
    
    global running
    while running:
        try:
            # Record the start time for measuring collection duration
            collection_start_time = time.time()
            
            # Check for interval updates periodically
            current_time = time.time()
            if current_time - last_check_time > check_interval:
                check_for_interval_update()
                last_check_time = current_time
                
            # Get timestamp and sensor readings
            timestamp = datetime.now().strftime('%d-%H:%M:%S.%f')
            soil_moisture = sensors.soil_moisture()
            temperature = sensors.temp()
            nh3 = sensors.nh3()
            humidity = sensors.humidity()
            pressure = sensors.pressure()
            light = sensors.light()
            oxidising = sensors.oxidising()
            reducing = sensors.reducing()
            
            # Create data row
            data_row = [
                timestamp,
                soil_moisture,
                temperature,
                nh3,
                humidity,
                pressure,
                light,
                oxidising,
                reducing
            ]
            
            # Add to cache
            cache.append(data_row)
            
            # Log the collected data
            logger.debug(f"Collected: {data_row}")
            
            # Save to Django database
            try:
                PlantData.objects.create(
                    temperature=temperature,
                    humidity=humidity,
                    soil_moisture=soil_moisture,
                    air_quality=nh3,
                    light=light,
                    pressure=pressure,
                    oxidising=oxidising,
                    reducing=reducing
                )
                logger.debug("Data saved to database successfully")
            except Exception as e:
                logger.error(f"Error saving to database: {str(e)}")
            
            # If cache reaches the defined size, write to CSV
            if len(cache) >= cache_size:
                with open(file_name, "a") as f:
                    writer = csv.writer(f)
                    writer.writerows(cache)
                logger.info(f"Wrote {len(cache)} records to CSV")
                cache = []
            
            # Calculate how long the collection took
            collection_duration = time.time() - collection_start_time
            
            # Update system status with collection timing
            update_system_status(collection_duration)
            
            # Calculate sleep time (accounting for the time taken to collect)
            sleep_time = max(0, data_collection_interval - collection_duration)
            
            # Sleep until next collection time
            time.sleep(sleep_time)
            
        except Exception as e:
            logger.error(f"Error during data collection: {str(e)}")
            time.sleep(1)  # Short delay before retrying after error

    # Write any remaining data before exiting
    if cache:
        with open(file_name, "a") as f:
            writer = csv.writer(f)
            writer.writerows(cache)
        logger.info(f"Wrote final {len(cache)} records to CSV")

    logger.info("Data collection stopped")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}")
        sys.exit(1) 