from typing import Type
from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import Serializer

from ..models import Appointment, HealthcareProvider, HealthcareProviderProfile
from ..serializers.healthcare_provider import (
    HealthcareProviderProfileSerializer,
    HealthcareProviderProfileCreateSerializer, 
    HealthcareProviderListSerializer
)
from ..services.healthcare_provider import HealthcareProviderService

@method_decorator(ratelimit(key="ip", rate="50/h", method="GET"), name='get')
class HealthcareProviderListView(generics.ListAPIView):
    queryset = HealthcareProviderProfile.objects.filter(
        is_removed=False,
        user__is_active=True
    ).select_related('user', 'speciality', 'primary_hospital')
    serializer_class = HealthcareProviderListSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'speciality': ['exact'],
        'primary_hospital': ['exact'], 
        'years_of_experience': ['gte', 'lte'],
        'fees': ['gte', 'lte'],
        'city': ['icontains'],
        'state': ['exact'],
    }
    search_fields = [
        'user__first_name',
        'user__last_name', 
        'speciality__name',
        'about',
        'city'
    ]
    ordering_fields = ['years_of_experience', 'fees', 'created_at']
    ordering = ['-years_of_experience']

class HealthcareProviderProfileView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]

    queryset = HealthcareProviderProfile.objects.select_related(
        'user', 'speciality', 'primary_hospital'
    ).filter(is_removed=False)
    serializer_class = HealthcareProviderProfileSerializer
    lookup_field = 'id'

class MyHealthcareProviderProfileView(generics.RetrieveUpdateAPIView):
    """Get/update current user's healthcare provider profile"""
    permission_classes = [IsAuthenticated]
    serializer_class = HealthcareProviderProfileSerializer

    def get_object(self) -> HealthcareProviderProfile:
        profile = HealthcareProviderService.get_provider_profile(self.request.user)
        if not profile:
            raise ValidationError("Healthcare provider profile not found")
        return profile

    def get_serializer_class(self) -> Type[Serializer]:
        if self.request.method in ['PUT', 'PATCH']:
            return HealthcareProviderProfileCreateSerializer
        return HealthcareProviderProfileSerializer

class HealthcareProviderStatisticsView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            provider = HealthcareProvider.objects.get(user=request.user)
            profile = provider.profile
            
            upcoming_appointments = Appointment.objects.filter(
                healthcare_provider=provider,
                appointment_start_datetime_utc__gte=timezone.now(),
                status__in=[Appointment.Status.CONFIRMED, Appointment.Status.REQUESTED]
            ).count()
            
            completed_appointments = Appointment.objects.filter(
                healthcare_provider=provider,
                status=Appointment.Status.COMPLETED
            ).count()
            
            return Response({
                'profile': HealthcareProviderProfileSerializer(profile).data,
                'stats': {
                    'upcoming_appointments': upcoming_appointments,
                    'completed_appointments': completed_appointments,
                    'years_of_experience': profile.years_of_experience,
                    'fees': profile.fees,
                }
            })
        except HealthcareProvider.DoesNotExist:
            return Response(
                {"detail": "Healthcare provider profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )