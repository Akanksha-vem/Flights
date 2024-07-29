# flights/serializers.py
from rest_framework import serializers

class FlightSummarySerializer(serializers.Serializer):
        access = serializers.CharField(max_length=255)

class PlaceDateSerializer(serializers.Serializer):
    place = serializers.CharField(max_length=100)
    date = serializers.DateField()
    access = serializers.CharField(max_length=255)

    

class DateSerializer(serializers.Serializer):
    date = serializers.DateField()
    access = serializers.CharField(max_length=255)

class FlightSerializer(serializers.Serializer):
    flight_id = serializers.CharField()
    origin = serializers.CharField()
    destination = serializers.CharField()
    departure_time = serializers.DateTimeField()
    arrival_time = serializers.DateTimeField()
    # Other fields as needed
    from rest_framework import serializers

class PlaceSerializer(serializers.Serializer):
    place = serializers.CharField(max_length=100)
    access = serializers.CharField(max_length=255)



