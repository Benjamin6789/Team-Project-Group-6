# monitoring/models.py
from django.db import models

class PlantData(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    temperature = models.FloatField()
    humidity = models.FloatField()
    soil_moisture = models.FloatField()
    air_quality = models.FloatField()
    light = models.FloatField(null=True, blank=True)
    pressure = models.FloatField(null=True, blank=True)
    oxidising = models.FloatField(null=True, blank=True)
    reducing = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"Plant Data at {self.timestamp}"

class SystemStatus(models.Model):
    timestamp = models.DateTimeField(auto_now=True)
    last_collection_time = models.DateTimeField(null=True, blank=True)
    collection_duration = models.FloatField(default=0.0)  # Time in seconds
    is_collecting_delayed = models.BooleanField(default=False)
    status_message = models.CharField(max_length=255, blank=True)
    
    @classmethod
    def get_current_status(cls):
        """Get or create the current system status object"""
        status, created = cls.objects.get_or_create(pk=1)
        return status
    
    def __str__(self):
        return f"System Status at {self.timestamp}"
