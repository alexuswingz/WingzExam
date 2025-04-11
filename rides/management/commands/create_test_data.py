from django.core.management.base import BaseCommand
from rides.models import Ride, RideEvent, User
from django.utils import timezone
from datetime import timedelta
import random

class Command(BaseCommand):
    help = 'Creates test data with many ride events'

    def add_arguments(self, parser):
        parser.add_argument('--rides', type=int, default=5, help='Number of rides to create')
        parser.add_argument('--events_per_ride', type=int, default=100, help='Number of events per ride')

    def handle(self, *args, **options):
        ride_count = options['rides']
        events_per_ride = options['events_per_ride']
        
        # Create users if they don't exist
        rider, created = User.objects.get_or_create(
            username='testrider',
            defaults={
                'email': 'rider@example.com',
                'role': 'user',
                'first_name': 'Test',
                'last_name': 'Rider',
                'phone_number': '555-123-4567',
                'is_active': True
            }
        )
        if created:
            rider.set_password('password')
            rider.save()
            self.stdout.write(self.style.SUCCESS(f'Created rider user: {rider.username}'))
        
        driver, created = User.objects.get_or_create(
            username='testdriver',
            defaults={
                'email': 'driver@example.com',
                'role': 'user',
                'first_name': 'Test',
                'last_name': 'Driver',
                'phone_number': '555-987-6543',
                'is_active': True
            }
        )
        if created:
            driver.set_password('password')
            driver.save()
            self.stdout.write(self.style.SUCCESS(f'Created driver user: {driver.username}'))
            
        # Create admin user
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'role': 'admin',
                'first_name': 'Admin',
                'last_name': 'User',
                'phone_number': '555-000-0000',
                'is_active': True,
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin.set_password('password')
            admin.save()
            self.stdout.write(self.style.SUCCESS(f'Created admin user: {admin.username}'))
            
        # Create rides
        for i in range(ride_count):
            ride = Ride.objects.create(
                pickup_latitude=40.7128 + (random.random() * 0.1),
                pickup_longitude=-74.0060 + (random.random() * 0.1),
                dropoff_latitude=40.7128 + (random.random() * 0.1),
                dropoff_longitude=-74.0060 + (random.random() * 0.1),
                pickup_time=timezone.now() + timedelta(hours=i),
                id_rider=rider,
                id_driver=driver,
                status="COMPLETED"
            )
            self.stdout.write(self.style.SUCCESS(f'Created ride {i+1}/{ride_count}'))
            
            # Create many events for each ride
            for j in range(events_per_ride):
                # Create a mix of old and recent events
                if j < events_per_ride - 5:  # Most events are old
                    event_time = timezone.now() - timedelta(days=random.randint(2, 30))
                else:  # A few events are from the last 24 hours
                    event_time = timezone.now() - timedelta(hours=random.randint(1, 23))
                
                status_descriptions = {
                    0: ("REQUESTED", "Ride requested"),
                    1: ("IN_PROGRESS", "Ride started"),
                    2: ("COMPLETED", "Ride completed")
                }
                
                event_type = min(j // (events_per_ride // 3), 2)
                old_status = status_descriptions[max(0, event_type-1)][0] if event_type > 0 else None
                new_status = status_descriptions[event_type][0]
                description = status_descriptions[event_type][1]
                
                RideEvent.objects.create(
                    id_ride=ride,
                    description=description,
                    old_status=old_status,
                    new_status=new_status,
                    user=driver if j % 2 == 0 else rider,
                    created_at=event_time
                )
            
            self.stdout.write(self.style.SUCCESS(f'Created {events_per_ride} events for ride {i+1}'))
        
        self.stdout.write(self.style.SUCCESS(f'Created {ride_count} rides with {events_per_ride} events each'))
        self.stdout.write(self.style.SUCCESS(f'Total: {ride_count * events_per_ride} ride events created')) 