from django.shortcuts import render
from rest_framework import viewsets, permissions, filters
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from django.db.models import F, ExpressionWrapper, FloatField, Prefetch, Count
from django.db.models.functions import Power, Sqrt
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from .models import Ride, RideEvent, User
from .serializers import RideSerializer, UserSerializer, RideEventSerializer
from .permissions import IsAdminUser
from rest_framework.pagination import PageNumberPagination
from django.db import connection, reset_queries
import json
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser as DRFIsAdminUser

class RidePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API viewset for retrieving user information
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

class RideEventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API viewset for retrieving ride event information
    """
    queryset = RideEvent.objects.all().order_by('-created_at')
    serializer_class = RideEventSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        ride_id = self.request.query_params.get('ride_id')
        if ride_id:
            queryset = queryset.filter(id_ride=ride_id)
        return queryset

class RideViewSet(viewsets.ModelViewSet):
    """
    API viewset for handling ride operations
    """
    queryset = Ride.objects.all()
    serializer_class = RideSerializer
    permission_classes = [IsAdminUser]
    pagination_class = RidePagination
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['pickup_time', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        # Get events from the last 24 hours
        last_24_hours = timezone.now() - timedelta(hours=24)
        todays_events = RideEvent.objects.filter(
            created_at__gte=last_24_hours
        ).select_related('user')
        
        # Base queryset with select_related to minimize queries
        queryset = Ride.objects.all().select_related(
            'id_rider', 
            'id_driver'
        ).prefetch_related(
            # Use Prefetch to customize the related objects that are retrieved
            Prefetch(
                'events',
                queryset=todays_events,
                to_attr='todays_events'
            )
        )
        
        # Filter by status
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status.upper())
        
        # Filter by rider email
        rider_email = self.request.query_params.get('rider_email')
        if rider_email:
            queryset = queryset.filter(id_rider__email__icontains=rider_email)
        
        # Sort by distance to pickup if lat/lng provided
        lat = self.request.query_params.get('lat')
        lng = self.request.query_params.get('lng')
        sort_by_distance = self.request.query_params.get('sort_by_distance')
        
        if lat and lng and sort_by_distance:
            try:
                lat = float(lat)
                lng = float(lng)
                
                # Calculate distance using the Pythagorean theorem
                # For production, consider using PostGIS for geographic distance calculations
                queryset = queryset.annotate(
                    distance=ExpressionWrapper(
                        Sqrt(
                            Power(F('pickup_latitude') - lat, 2) + 
                            Power(F('pickup_longitude') - lng, 2)
                        ),
                        output_field=FloatField()
                    )
                ).order_by('distance')
            except (ValueError, TypeError):
                # If conversion fails, ignore the distance sorting
                pass
                
        return queryset
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        ride = self.get_object()
        if ride.status in ['COMPLETED', 'CANCELLED']:
            return Response(
                {'error': 'Cannot cancel a completed or already cancelled ride'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_status = ride.status
        ride.status = 'CANCELLED'
        ride.save()
        
        # Create a RideEvent for the cancellation
        RideEvent.objects.create(
            id_ride=ride,
            description=f"Ride cancelled",
            old_status=old_status,
            new_status='CANCELLED',
            user=request.user if hasattr(request, 'user') else None,
            created_at=timezone.now()
        )
        
        return Response({'status': 'Ride cancelled'})
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        ride = self.get_object()
        if ride.status != 'REQUESTED':
            return Response(
                {'error': 'Only requested rides can be started'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        driver_id = request.data.get('driver_id')
        if not driver_id:
            return Response(
                {'error': 'Driver ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            driver = User.objects.get(id_user=driver_id)
            old_status = ride.status
            ride.id_driver = driver
            ride.status = 'IN_PROGRESS'
            ride.save()
            
            # Create a RideEvent for starting the ride
            RideEvent.objects.create(
                id_ride=ride,
                description=f"Ride started with driver {driver.first_name} {driver.last_name}",
                old_status=old_status,
                new_status='IN_PROGRESS',
                user=driver,
                created_at=timezone.now()
            )
            
            return Response({'status': 'Ride started'})
        except User.DoesNotExist:
            return Response(
                {'error': 'Driver not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        ride = self.get_object()
        if ride.status != 'IN_PROGRESS':
            return Response(
                {'error': 'Only in-progress rides can be completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_status = ride.status
        ride.status = 'COMPLETED'
        ride.save()
        
        # Create a RideEvent for completing the ride
        RideEvent.objects.create(
            id_ride=ride,
            description="Ride completed",
            old_status=old_status,
            new_status='COMPLETED',
            user=ride.id_driver,
            created_at=timezone.now()
        )
        
        return Response({'status': 'Ride completed'})
        
    @action(detail=True, methods=['get'])
    def events(self, request, pk=None):
        ride = self.get_object()
        events = ride.events.all().order_by('-created_at')
        serializer = RideEventSerializer(events, many=True)
        return Response(serializer.data)
        
    @action(detail=False, methods=['get'])
    def query_stats(self, request):
        """
        Debug endpoint to show the number of queries executed
        """
        # Reset query log
        reset_queries()
        
        # Perform the query with our optimized queryset
        queryset = self.get_queryset()
        rides = self.paginate_queryset(queryset)
        serializer = self.get_serializer(rides, many=True)
        response = self.get_paginated_response(serializer.data)
        
        # Get query information
        query_count = len(connection.queries)
        query_details = connection.queries
        
        response.data['query_stats'] = {
            'total_queries': query_count,
            'queries': query_details
        }
        
        return response

@api_view(['GET'])
@permission_classes([DRFIsAdminUser])
def query_performance(request):
    """
    Compare optimized vs unoptimized query performance
    """
    # Get the count of RideEvents to display in the response
    total_events = RideEvent.objects.count()
    rides_count = Ride.objects.count()
    
    # Test 1: Unoptimized approach (loads all events)
    reset_queries()
    
    # Unoptimized query - loads all events for all rides
    rides_unoptimized = Ride.objects.all().select_related('id_rider', 'id_driver').prefetch_related('events')[:10]
    
    # Force evaluation of the queryset
    list(rides_unoptimized)
    
    unoptimized_query_count = len(connection.queries)
    
    # Test 2: Optimized approach (only loads today's events)
    reset_queries()
    
    # Get events from the last 24 hours
    last_24_hours = timezone.now() - timedelta(hours=24)
    todays_events = RideEvent.objects.filter(created_at__gte=last_24_hours).select_related('user')
    
    # Optimized query - only loads events from last 24 hours
    rides_optimized = Ride.objects.all().select_related('id_rider', 'id_driver').prefetch_related(
        Prefetch('events', queryset=todays_events, to_attr='todays_events')
    )[:10]
    
    # Force evaluation of the queryset
    rides_list = list(rides_optimized)
    
    # Access todays_events for each ride to ensure it's loaded
    for ride in rides_list:
        list(ride.todays_events)
    
    optimized_query_count = len(connection.queries)
    
    # Calculate events loaded in each approach
    all_events_loaded = sum(ride.events.count() for ride in rides_unoptimized)
    todays_events_loaded = sum(len(ride.todays_events) for ride in rides_optimized)
    
    return Response({
        'database_stats': {
            'total_rides': rides_count,
            'total_events': total_events,
            'events_per_ride_avg': total_events / rides_count if rides_count > 0 else 0
        },
        'unoptimized_approach': {
            'query_count': unoptimized_query_count,
            'events_loaded': all_events_loaded,
            'description': 'Loads ALL events for each ride'
        },
        'optimized_approach': {
            'query_count': optimized_query_count,
            'events_loaded': todays_events_loaded,
            'description': 'Loads ONLY events from last 24 hours'
        },
        'improvement': {
            'query_reduction': f"{unoptimized_query_count - optimized_query_count} fewer queries",
            'data_reduction': f"{all_events_loaded - todays_events_loaded} fewer events loaded"
        }
    })
