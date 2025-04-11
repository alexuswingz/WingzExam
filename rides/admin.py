from django.contrib import admin
from .models import Ride, RideEvent, User

class RideEventInline(admin.TabularInline):
    model = RideEvent
    readonly_fields = ('old_status', 'new_status', 'user', 'created_at')
    extra = 0
    can_delete = False

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id_user', 'username', 'first_name', 'last_name', 'email', 'role')
    list_filter = ('role', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')

@admin.register(Ride)
class RideAdmin(admin.ModelAdmin):
    list_display = ('id_ride', 'pickup_time', 'id_rider', 'id_driver', 'status')
    list_filter = ('status',)
    search_fields = ('id_rider__username', 'id_driver__username')
    raw_id_fields = ('id_rider', 'id_driver')
    inlines = [RideEventInline]

@admin.register(RideEvent)
class RideEventAdmin(admin.ModelAdmin):
    list_display = ('id_ride_event', 'id_ride', 'old_status', 'new_status', 'user', 'created_at')
    list_filter = ('new_status',)
    search_fields = ('id_ride__id_ride', 'user__username')
    readonly_fields = ('id_ride', 'old_status', 'new_status', 'user', 'created_at')
