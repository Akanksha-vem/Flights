from django.db import models

# Create your models here.
from django.db import models

class Flight(models.Model):
    flight_id = models.CharField(max_length=100, unique=True)
    origin = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    # Other fields as needed

    def __str__(self):
        return f"{self.flight_id} from {self.origin} to {self.destination}"

