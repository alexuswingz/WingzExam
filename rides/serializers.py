from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from .models import Ride, RideEvent, User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id_user', 'username', 'first_name', 'last_name', 'email', 'phone_number', 'role')

class RideEventSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = RideEvent
        fields = ('id_ride_event', 'id_ride', 'description', 'old_status', 'new_status', 'user', 'created_at')
        read_only_fields = ('id_ride_event', 'created_at')

class RideSerializer(serializers.ModelSerializer):
    rider = serializers.SerializerMethodField()
    rider_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        source='id_rider',
        write_only=True
    )
    driver = serializers.SerializerMethodField()
    driver_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        source='id_driver',
        write_only=True,
        required=False
    )
    todays_ride_events = serializers.SerializerMethodField()
    distance = serializers.FloatField(read_only=True, required=False)
    
    def get_rider(self, obj):
        return UserSerializer(obj.id_rider).data
    
    def get_driver(self, obj):
        if obj.id_driver:
            return UserSerializer(obj.id_driver).data
        return None
    
    def get_todays_ride_events(self, obj):
        return RideEventSerializer(obj.todays_events, many=True).data
    
    class Meta:
        model = Ride
        fields = (
            'id_ride', 'pickup_latitude', 'pickup_longitude',
            'dropoff_latitude', 'dropoff_longitude',
            'pickup_time', 'rider', 'rider_id', 'driver', 'driver_id', 
            'status', 'created_at', 'updated_at', 'todays_ride_events', 'distance'
        )
        read_only_fields = ('created_at', 'updated_at', 'distance') 