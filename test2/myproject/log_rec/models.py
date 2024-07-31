# models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class APILog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    method = models.CharField(max_length=10)
    endpoint = models.CharField(max_length=255)
    parameters = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user} {self.method} {self.endpoint} {self.timestamp}"
