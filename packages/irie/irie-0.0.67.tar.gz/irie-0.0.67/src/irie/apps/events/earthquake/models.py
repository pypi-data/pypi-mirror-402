from django.db import models

class AccelerationSeries(models.Model):
    data = models.FileField(upload_to="timeseries/")
    sampling_rate = models.FloatField()
    units = models.CharField(max_length=20)

class EarthquakeRecord(models.Model):
    magnitude = models.FloatField()
    depth = models.FloatField()
    location = models.CharField(max_length=100)

    def __str__(self):
        return f"Magnitude: {self.magnitude}, Depth: {self.depth}, Location: {self.location}"