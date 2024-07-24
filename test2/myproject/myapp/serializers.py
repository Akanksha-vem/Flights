# myapp/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import OneTimeToken
from django import forms
#from .models import Flight

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'password', 'first_name', 'last_name']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class OneTimeTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = OneTimeToken
        fields = ['token']


# myapp/serializers.py
from rest_framework import serializers
from .models import Flight

class FlightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flight
        fields = ['flight_number']





