from django.db import models
from django.contrib.auth.models import User
from django.db import models

class Trip(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    destination = models.CharField(max_length=100)
    departure_date = models.DateField()
    return_date = models.DateField()
    budget = models.IntegerField()
    preferences_used = models.JSONField(null=True, blank=True)  # e.g., ["culture", "beach"]
    results_json = models.JSONField(null=True, blank=True)  # stores the full itinerary
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s trip to {self.destination}"


class UserPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    activities = models.JSONField()
    budget = models.IntegerField()
    preferred_climate = models.CharField(max_length=50, null=True)
# Create your models here.
