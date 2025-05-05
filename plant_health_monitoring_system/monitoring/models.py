# monitoring/models.py
from django.db import models

class PlantData(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    temperature = models.FloatField()
    humidity = models.FloatField()
    soil_moisture = models.FloatField()
    air_quality = models.FloatField()

    def __str__(self):
        return f"Plant Data at {self.timestamp}"
