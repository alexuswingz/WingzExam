# Ride Management API

A RESTful API built with Django REST Framework for managing ride information.

## Setup

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Apply migrations:
   ```
   python manage.py migrate
   ```
   
   > **Note:** Make sure all Django system tables are created by running:
   > ```
   > python manage.py migrate sessions
   > python manage.py migrate admin
   > python manage.py migrate contenttypes
   > python manage.py migrate authtoken
   > ```
   > This ensures all required Django system tables are created, preventing errors like "no such table: django_session".

4. Create an admin user and get an authentication token:
   ```
   python manage.py create_admin --username=adminuser --email=admin@example.com --password=secure_password
   ```
5. Run the development server:
   ```
   python manage.py runserver
   ```

## Implementation Process

### Backend Implementation

1. **Project Setup**
   - Created a new Django project `ride_management`
   - Set up Django REST Framework
   - Configured authentication using Django's TokenAuthentication

2. **Data Models Creation**
   - Created a custom User model extending AbstractBaseUser
   - Created Ride model with foreign keys to User for rider and driver
   - Created RideEvent model to track ride status changes and events
   - Added optimized index fields for better query performance

3. **Migration Management**
   - Created initial migrations for models
   - Handled unique constraints and foreign key relationships
   - Added database indexes on frequently queried fields

4. **API Endpoints Development**
   - Created ViewSets for User, Ride, and RideEvent models
   - Implemented pagination for large datasets
   - Added filtering and sorting capabilities
   - Created custom actions for ride operations (start, cancel, complete)

5. **Query Optimization**
   - Used `select_related` for eager loading of related models
   - Implemented custom `Prefetch` objects to filter related data
   - Added filtered prefetching for ride events to only load recent events
   - Created performance comparison endpoints to demonstrate optimization

6. **Custom Management Commands**
   - Created `create_admin` command for quick admin user creation
   - Implemented `create_test_data` command to populate the database with sample rides and events

7. **Permissions and Authentication**
   - Configured Token-based authentication
   - Created custom permission classes
   - Secured all API endpoints with appropriate permissions

8. **Testing and Debugging**
   - Added query debugging endpoints
   - Created comparison endpoints to demonstrate performance improvements
   - Implemented error handling throughout the application

## Authentication

The API uses token-based authentication. Only users with admin privileges can access the API endpoints.

### Getting a Token

You can obtain an authentication token in two ways:

1. Running the `create_admin` command:
   ```
   python manage.py create_admin
   ```
   
2. Using the token endpoint with existing credentials:
   ```
   POST /api-token-auth/
   Content-Type: application/json
   
   {
     "username": "adminuser",
     "password": "secure_password"
   }
   ```

### Using the Token

Include the token in your API requests:

```
GET /api/rides/
Authorization: Token <your_token>
```

## API Endpoints

### Users
- **List Users**:
  - `GET /api/users/`
  - Lists all users

- **Retrieve User**:
  - `GET /api/users/{id}/`
  - Retrieves a specific user

### Rides

- **List/Create Rides**:
  - `GET /api/rides/`
  - Lists all rides or creates a new ride
  - Supports pagination, filtering, and sorting (see details below)

- **Retrieve/Update/Delete Ride**:
  - `GET/PUT/PATCH/DELETE /api/rides/{id}/`
  - Retrieves, updates or deletes a specific ride

#### Ride List API Features

The Ride List API (`GET /api/rides/`) supports:

1. **Pagination**:
   - `?page=2` - Get the second page of results
   - `?page_size=20` - Set the page size (default: 10, max: 100)

2. **Filtering**:
   - `?status=REQUESTED` - Filter by ride status
   - `?rider_email=example@mail.com` - Filter by rider email

3. **Sorting**:
   - `?ordering=pickup_time` - Sort by pickup time (ascending)
   - `?ordering=-pickup_time` - Sort by pickup time (descending)
   - `?ordering=created_at` - Sort by creation date
   - Other orderable fields: `updated_at`

4. **Distance-based Sorting**:
   - `?lat=40.7128&lng=-74.0060&sort_by_distance=true` - Sort rides by distance from the given GPS coordinates
   - This is optimized for large datasets with database indexes

5. **Performance Optimization**:
   - The API includes a `todays_ride_events` field for each ride that only retrieves events from the last 24 hours
   - This significantly reduces the query load for large datasets
   - The implementation uses only 2-3 database queries regardless of the number of rides or events

### Ride Events

- **List Events**:
  - `GET /api/events/`
  - Lists all ride events

- **Retrieve Event**:
  - `GET /api/events/{id}/`
  - Retrieves a specific event

- **List Events for Ride**:
  - `GET /api/rides/{id}/events/`
  - Lists all events for a specific ride

### Custom Actions

- **Cancel Ride**:
  - `POST /api/rides/{id}/cancel/`
  - Cancels an existing ride

- **Start Ride**:
  - `POST /api/rides/{id}/start/`
  - Starts a requested ride (requires driver_id)

- **Complete Ride**:
  - `POST /api/rides/{id}/complete/`
  - Marks an in-progress ride as completed

### Performance Debugging

- **Query Statistics**:
  - `GET /api/rides/query_stats/`
  - Returns the ride list along with detailed performance information
  - Shows the total number of database queries executed
  - Useful for debugging and confirming optimization

- **Performance Comparison**:
  - `GET /api/performance/`
  - Compares optimized vs unoptimized query performance
  - Shows the reduction in queries and data loaded

## Data Models

- **User**:
  - `id_user`: Int - Primary key 
  - `role`: String - User role ('admin' or other roles)
  - `first_name`: String - User's first name
  - `last_name`: String - User's last name
  - `email`: String - User's email address
  - `phone_number`: String - User's phone number
  - Plus additional fields for Django authentication compatibility

- **Ride**:
  - `id_ride`: Int - Primary key
  - `status`: String - Ride status (e.g., 'REQUESTED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED')
  - `id_rider`: ForeignKey to User - The person requesting the ride
  - `id_driver`: ForeignKey to User (optional) - The driver assigned to the ride
  - `pickup_latitude`: Float - Latitude of pickup location
  - `pickup_longitude`: Float - Longitude of pickup location
  - `dropoff_latitude`: Float - Latitude of dropoff location
  - `dropoff_longitude`: Float - Longitude of dropoff location
  - `pickup_time`: DateTime - The scheduled pickup time
  - `created_at`: DateTime - When the ride was created
  - `updated_at`: DateTime - When the ride was last updated

- **RideEvent**:
  - `id_ride_event`: Int - Primary key
  - `id_ride`: ForeignKey to Ride - The related ride
  - `description`: String - Description of the ride event
  - `old_status`: String - The previous status (null for new rides)
  - `new_status`: String - The new status
  - `user`: ForeignKey to User - The user who created the event
  - `created_at`: DateTime - Timestamp of when the event occurred

## Performance Considerations

The Ride List API is optimized for large datasets:

1. **Query Efficiency**:
   - The `todays_ride_events` field uses a filtered Prefetch to retrieve only recent events
   - This approach uses only 2-3 database queries regardless of the size of the dataset
   - Indexing is used on frequently filtered and sorted fields

2. **Indexing Strategy**:
   - Database indexes are applied to `status`, `pickup_time`, `id_rider` & `id_driver` foreign keys
   - Composite indexes for common query patterns
   - Location fields are indexed for efficient distance calculations

3. **Preloading Strategy**:
   - Foreign keys are loaded using `select_related` to avoid N+1 query issues
   - Related events are loaded using customized `Prefetch` objects to filter data at the database level

## Admin Interface

The admin interface is available at `/admin/` and provides a way to manage all models through a user-friendly interface.

## Technologies Used

- Django 5.2
- Django REST Framework
- SQLite (for development)
- Token Authentication 