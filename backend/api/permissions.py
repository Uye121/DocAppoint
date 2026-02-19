from rest_framework import permissions


# Didn't add type signature due to Pylance Override Error
class IsPatient(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, "patient")
        )


class IsHealthcareProvider(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, "provider")
        )

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsStaffOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        return (
            user.is_staff
            or hasattr(user, "system_admin")
            or hasattr(user, "admin_staff")
        )


class IsPatientOrProvider(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        return user.is_staff or hasattr(user, "patient") or hasattr(user, "provider")


class IsRecordOwner(permissions.BasePermission):
    """Check if user is the owner of the medical record"""

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        if hasattr(request.user, "provider"):
            return obj.healthcare_provider == request.user.provider

        if request.user.is_staff:
            return True

        return False
