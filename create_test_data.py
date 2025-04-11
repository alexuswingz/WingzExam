#!/usr/bin/env python
import os
import sys
import django
import random
from datetime import datetime, timedelta
import time

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ride_management.settings')
django.setup()

from django.contrib.auth.hashers import make_password
from rides.models import User, Ride, RideEvent

def create_users():
    """Create admin, drivers and riders"""
    print("Creating users...")
    
    # Create admin user
    admin = User.objects.create(
        username="admin",
        email="admin@wingz.com",
        password=make_password("admin123"),
        first_name="Admin",
        last_name="User",
        phone_number="555-123-4567",
        role="admin",
        is_staff=True,
        is_superuser=True
    )
    
    # Create drivers
    drivers = []
    for i in range(1, 4):
        driver = User.objects.create(
            username=f"driver{i}",
            email=f"driver{i}@wingz.com",
            password=make_password(f"driver{i}"),
            first_name=f"Test",
            last_name=f"Driver{i}",
            phone_number=f"555-{100+i}-{1000+i}",
            role="driver"
        )
        drivers.append(driver)
    
    # Create riders
    riders = []
    for i in range(1, 6):
        rider = User.objects.create(
            username=f"rider{i}",
            email=f"rider{i}@example.com",
            password=make_password(f"rider{i}"),
            first_name=f"Test",
            last_name=f"Rider{i}",
            phone_number=f"555-{200+i}-{2000+i}",
            role="user"
        )
        riders.append(rider)
    
    return admin, drivers, riders

def create_rides(drivers, riders):
    """Create rides with different statuses"""
    print("Creating rides...")
    
    rides = []
    statuses = ['REQUESTED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED']
    now = datetime.now()
    
    # Create rides with different dates
    for i in range(1, 50):
        # Randomize the date within the last week
        hours_ago = random.randint(0, 168)  # Within a week
        pickup_time = now - timedelta(hours=hours_ago)
        
        # Status based on pickup time
        if hours_ago > 120:  # More than 5 days ago
            status = 'COMPLETED'
            driver = random.choice(drivers)
        elif hours_ago > 72:  # More than 3 days ago
            status = random.choice(['COMPLETED', 'CANCELLED'])
            driver = random.choice(drivers) if status == 'COMPLETED' else None
        elif hours_ago > 24:  # More than 1 day ago
            status = random.choice(['IN_PROGRESS', 'COMPLETED'])
            driver = random.choice(drivers)
        else:  # Recent rides
            status = random.choice(statuses)
            driver = random.choice(drivers) if status in ['IN_PROGRESS', 'COMPLETED'] else None
        
        # Create the ride
        ride = Ride.objects.create(
            id_rider=random.choice(riders),
            id_driver=driver,
            status=status,
            pickup_latitude=random.uniform(37.7, 37.8),
            pickup_longitude=random.uniform(-122.5, -122.4),
            dropoff_latitude=random.uniform(37.7, 37.8),
            dropoff_longitude=random.uniform(-122.5, -122.4),
            pickup_time=pickup_time,
        )
        rides.append(ride)
    
    return rides

def create_ride_events(rides, drivers):
    """Create ride events for the rides"""
    print("Creating ride events...")
    
    events = []
    for ride in rides:
        # Number of events depends on status
        if ride.status == 'COMPLETED':
            num_events = random.randint(3, 7)
        elif ride.status == 'IN_PROGRESS':
            num_events = random.randint(2, 4)
        elif ride.status == 'CANCELLED':
            num_events = random.randint(1, 3)
        else:  # REQUESTED
            num_events = random.randint(1, 2)
        
        # Always create a "Ride requested" event
        requested_event = RideEvent.objects.create(
            id_ride=ride,
            description="Ride requested",
            old_status=None,
            new_status="REQUESTED",
            user=ride.id_rider,
            created_at=ride.pickup_time - timedelta(hours=random.randint(1, 5))
        )
        events.append(requested_event)
        
        current_status = "REQUESTED"
        event_time = requested_event.created_at + timedelta(minutes=random.randint(5, 30))
        
        # Add a driver assigned event if ride has progressed beyond REQUESTED
        if ride.status != 'REQUESTED' and num_events > 1:
            assigned_event = RideEvent.objects.create(
                id_ride=ride,
                description=f"Driver {ride.id_driver.first_name} {ride.id_driver.last_name} assigned",
                old_status=current_status,
                new_status="IN_PROGRESS",
                user=ride.id_driver,
                created_at=event_time
            )
            events.append(assigned_event)
            current_status = "IN_PROGRESS"
            event_time += timedelta(minutes=random.randint(5, 30))
        
        # Add completion or cancellation event
        if ride.status in ['COMPLETED', 'CANCELLED'] and num_events > 2:
            user = ride.id_driver if ride.status == 'COMPLETED' else ride.id_rider
            final_event = RideEvent.objects.create(
                id_ride=ride,
                description=f"Ride {ride.status.lower()}",
                old_status=current_status,
                new_status=ride.status,
                user=user,
                created_at=event_time
            )
            events.append(final_event)
        
        # Add some random events with recent timestamps for today's events
        if random.random() < 0.3:  # 30% of rides get some events today
            for _ in range(random.randint(1, 5)):
                hours_ago = random.randint(0, 24)
                recent_time = datetime.now() - timedelta(hours=hours_ago)
                user = random.choice([ride.id_rider, ride.id_driver]) if ride.id_driver else ride.id_rider
                event = RideEvent.objects.create(
                    id_ride=ride,
                    description=f"System notification: {random.choice(['GPS update', 'ETA update', 'Traffic alert', 'Payment processed'])}",
                    old_status=ride.status,
                    new_status=ride.status,
                    user=user,
                    created_at=recent_time
                )
                events.append(event)
    
    return events

def main():
    """Main function to execute data creation"""
    # Clear existing data first
    # Already done with flush
    
    # Create test data
    start_time = time.time()
    print("Starting test data creation...")
    
    admin, drivers, riders = create_users()
    rides = create_rides(drivers, riders)
    events = create_ride_events(rides, drivers)
    
    total_time = time.time() - start_time
    
    # Print summary
    print("\nTest data created successfully!")
    print(f"Created {User.objects.count()} users ({len(drivers)} drivers, {len(riders)} riders)")
    print(f"Created {Ride.objects.count()} rides")
    print(f"Created {RideEvent.objects.count()} ride events")
    print(f"Total time: {total_time:.2f} seconds")

if __name__ == "__main__":
    main() 