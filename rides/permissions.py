from rest_framework import permissions

class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to only allow admin users to access the API.
    """

    def has_permission(self, request, view):
        return bool(request.user and (request.user.is_superuser or 
                                      (hasattr(request.user, 'role') and request.user.role == 'admin'))) 