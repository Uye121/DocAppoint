# from typing import Optional, List
# from django.utils import timezone
# from django.db import transaction
# from django.core.exceptions import ValidationError
# from django.db.models import Q
# from django.contrib.auth import get_user_model

# from ..models import HealthcareProvider, Hospital, ProviderHospitalAssignment

# User = get_user_model()

# class HealthcareProviderService:
#     @staticmethod
#     @transaction.atomic
#     def create_provider(user: User, profile_data: dict) -> HealthcareProvider:
#         speciality = profile_data.get('speciality')
#         primary_hospital = profile_data.get('primary_hospital')
        
#         # Validate speciality
#         if not speciality:
#             raise ValidationError("Speciality is required")

#         if hasattr(speciality, 'is_removed') and speciality.is_removed:
#             raise ValidationError("This speciality is no longer available")
            
#         # Validate primary hospital assignment
#         if primary_hospital:
#             assignment = ProviderHospitalAssignment.objects.filter(
#                 provider__user=user,
#                 hospital=primary_hospital,
#                 is_active=True
#             ).first()
            
#             if not assignment:
#                 raise ValidationError(
#                     "Provider must be assigned to the primary hospital"
#                 )
        
#         profile = HealthcareProvider.objects.create(
#             user=user,
#             **profile_data
#         )
        
#         return profile

#     @staticmethod
#     def get_provider_profile(user: User) -> Optional[HealthcareProvider]:
#         try:
#             return HealthcareProviderProfile.objects.select_related(
#                 'user', 'speciality', 'primary_hospital'
#             ).get(user=user)
#         except HealthcareProviderProfile.DoesNotExist:
#             return None

#     @staticmethod
#     def search_providers(
#         speciality_id: Optional[int] = None,
#         hospital_id: Optional[int] = None,
#         min_experience: Optional[int] = None,
#         min_fees: Optional[float] = None,
#         max_fees: Optional[float] = None,
#         city: Optional[str] = None
#     ) -> List[HealthcareProviderProfile]:
#         """Search healthcare providers with filters"""
#         queryset = HealthcareProviderProfile.objects.select_related(
#             'user', 'speciality', 'primary_hospital'
#         ).filter(
#             is_removed=False,
#             user__is_active=True
#         )
        
#         if speciality_id:
#             queryset = queryset.filter(speciality_id=speciality_id)
        
#         if hospital_id:
#             queryset = queryset.filter(
#                 Q(primary_hospital_id=hospital_id) |
#                 Q(hospitals__id=hospital_id)
#             ).distinct()
        
#         if min_experience is not None:
#             queryset = queryset.filter(
#                 years_of_experience__gte=min_experience
#             )
        
#         if min_fees is not None:
#             queryset = queryset.filter(fees__gte=max_fees)
#         if max_fees is not None:
#             queryset = queryset.filter(fees__lte=max_fees)

#         if city:
#             queryset = queryset.filter(city__icontains=city)
        
#         return queryset.order_by('-years_of_experience', 'fees')

#     @staticmethod
#     @transaction.atomic 
#     def assign_to_hospital(
#         provider: HealthcareProviderProfile,
#         hospital: Hospital,
#         is_primary: bool = False
#     ) -> ProviderHospitalAssignment:
#         # Deactivate existing assignments to same hospital
#         ProviderHospitalAssignment.objects.filter(
#             provider=provider,
#             hospital=hospital,
#             end_datetime_utc__isnull=True
#         ).update(end_datetime_utc=timezone.now())
        
#         assignment = ProviderHospitalAssignment.objects.create(
#             provider=provider,
#             hospital=hospital,
#             is_active=True
#         )
        
#         if is_primary:
#             provider.primary_hospital = hospital
#             provider.save()
        
#         return assignment