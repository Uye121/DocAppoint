# Import all models for easy access
from .users import User, Patient, HealthcareProvider, AdminStaff, SystemAdmin
from .hospital import Hospital, ProviderHospitalAssignment
from .appointment import Appointment, Slot
from .medical import MedicalRecord
from .message import Message
from .speciality import Speciality

__all__ = [
    "User",
    "Patient",
    "HealthcareProvider",
    "AdminStaff",
    "SystemAdmin",
    "Hospital",
    "ProviderHospitalAssignment",
    "Appointment",
    "Slot",
    "MedicalRecord",
    "Message",
    "Speciality",
]
