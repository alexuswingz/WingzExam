from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RideViewSet, UserViewSet, RideEventViewSet, query_performance

router = DefaultRouter()
router.register(r'rides', RideViewSet)
router.register(r'users', UserViewSet)
router.register(r'events', RideEventViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('performance/', query_performance, name='query_performance'),
] 