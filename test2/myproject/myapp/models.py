from django.db import models

# Create your models here.
from django.contrib.auth.models import User
from django.db import models
import uuid
from django import forms


from django.contrib.auth.models import User

class OneTimeToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.token)

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'password', 'first_name', 'last_name']
# myapp/models.py
from django.db import models

# myapp/models.py
from django.db import models
from django.contrib.auth.models import User

class Flight(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    flight_number = models.CharField(max_length=100)
    #departure = models.CharField(max_length=100)
    #destination = models.CharField(max_length=100)
    #departure_time = models.DateTimeField()
    #arrival_time = models.DateTimeField()

    def __str__(self):
        return self.flight_number



# myapp/forms.py
from django import forms


from django.contrib.auth.models import User

