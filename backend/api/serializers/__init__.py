from .admin_staff import AdminStaffSerializer, AdminStaffCreateSerializer, AdminStaffOnBoardSerializer
from .auth import ChangePasswordSerializer, LoginSerializer
from .healthcare_provider import (
    HealthcareProviderSerializer, HealthcareProviderCreateSerializer,
    HealthcareProviderListSerializer, HealthcareProviderOnBoardSerializer
)
from .patient import PatientSerializer, PatientCreateSerializer, PatientOnBoardSerializer
from .speciality import SpecialitySerializer, SpecialityListSerializer, SpecialityCreateSerializer
from .system_admin import SystemAdminSerializer, SystemAdminCreateSerializer, SystemAdminOnBoardSerializer
from .user import UserSerializer
from .auth import ChangePasswordSerializer, LoginSerializer
from .appointment import (
    SlotSerializer,
    AppointmentListSerializer,
    AppointmentDetailSerializer,
    AppointmentCreateSerializer
)

__all__ = [
    'AdminStaffSerializer', 'AdminStaffCreateSerializer', 'AdminStaffOnBoardSerializer',
    'ChangePasswordSerializer', 'UserSerializer', 'LoginSerializer', 'HealthcareProviderSerializer',
    'HealthcareProviderCreateSerializer', 'HealthcareProviderListSerializer',
    'HealthcareProviderOnBoardSerializer', 'PatientSerializer', 'PatientCreateSerializer',
    'PatientOnBoardSerializer', 'SpecialitySerializer', 'SpecialityListSerializer',
    'SpecialityCreateSerializer', 'SystemAdminSerializer', 'SystemAdminCreateSerializer',
    'SystemAdminOnBoardSerializer', 'UserSerializer', 'ChangePasswordSerializer',
    'LoginSerializer', 'SlotSerializer', 'AppointmentListSerializer', 'AppointmentDetailSerializer',
    'AppointmentCreateSerializer'
]