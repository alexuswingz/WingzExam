from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone

class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        if not username:
            raise ValueError('Users must have a username')
        
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        
        return self.create_user(username, email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model matching the provided schema
    """
    id_user = models.AutoField(primary_key=True)
    role = models.CharField(max_length=50, default='user')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20)
    
    # Django authentication fields
    username = models.CharField(max_length=150, unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']
    
    class Meta:
        db_table = 'user'  # Match the schema name
        verbose_name = 'user'
        verbose_name_plural = 'users'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_short_name(self):
        return self.first_name

class Ride(models.Model):
    """
    Ride model matching the provided schema
    """
    id_ride = models.AutoField(primary_key=True)
    status = models.CharField(max_length=50, db_index=True)
    id_rider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rides_as_rider', to_field='id_user')
    id_driver = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='rides_as_driver', null=True, blank=True, to_field='id_user')
    pickup_latitude = models.FloatField(db_index=True)
    pickup_longitude = models.FloatField(db_index=True)
    dropoff_latitude = models.FloatField(default=0.0)
    dropoff_longitude = models.FloatField(default=0.0)
    pickup_time = models.DateTimeField(db_index=True)
    
    # Additional fields for compatibility with existing code
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ride'
    
    def __str__(self):
        return f"Ride {self.id_ride}: {self.status} - {self.pickup_time}"

class RideEvent(models.Model):
    """
    RideEvent model matching the provided schema
    """
    id_ride_event = models.AutoField(primary_key=True)
    id_ride = models.ForeignKey(Ride, on_delete=models.CASCADE, related_name='events', to_field='id_ride')
    description = models.CharField(max_length=255, default="Event recorded")
    created_at = models.DateTimeField(db_index=True, default=timezone.now)
    
    # Additional field to track user who created the event
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, to_field='id_user')
    
    # For compatibility with existing code
    old_status = models.CharField(max_length=50, null=True, blank=True)
    new_status = models.CharField(max_length=50, null=True, blank=True)
    
    class Meta:
        db_table = 'ride_event'
    
    def __str__(self):
        return f"Event {self.id_ride_event} for Ride {self.id_ride_id}: {self.description}"
