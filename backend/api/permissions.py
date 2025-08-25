from rest_framework import permissions

class AdminOnlyEdit(permissions.BasePermission):
    def has_permission(self, request, view):
        """
        Override default function to enforce action where only
        admin users can POST/PUT/PATCH/DELETE.

        Args:
            request (HTTPRequest): The incoming request object
            view (APIView): The view accessed

        Returns:
            bool: True if permission is granted, false otherwise.
        """
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_admin