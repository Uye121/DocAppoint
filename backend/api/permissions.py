from rest_framework import permissions

# Didn't add type signature due to Pylance Override Error
class IsPatient(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user
                and request.user.is_authenticated
                and hasattr(request.user,'patient'))

class IsHealthcareProvider(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user
                and request.user.is_authenticated
                and hasattr(request.user,'provider'))
    
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
    
class IsStaffOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        
        return (user.is_staff
                or hasattr(user, 'system_admin')
                or hasattr(user, 'admin_staff'))
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Staff and system admin can access any provider
        if user.is_staff or hasattr(user, 'system_admin'):
            return True
        
        # Hospital admin can only access providers from their hospital
        if hasattr(user, 'admin_staff'):
            return (
                obj.primary_hospital and
                obj.primary_hospital == user.admin_staff.hospital
            )
        
        return False
