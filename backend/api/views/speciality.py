from rest_framework import generics
from rest_framework.exceptions import ValidationError
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from rest_framework.permissions import IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser

from ..models import Speciality
from ..serializers.speciality import (
    SpecialitySerializer,
    SpecialityListSerializer,
    SpecialityCreateSerializer
)
from ..services.speciality import SpecialityService

@method_decorator(ratelimit(key="ip", rate="30/h", method="GET"), name='get')
class SpecialityListView(generics.ListAPIView):
    queryset = Speciality.objects.filter(is_removed=False).order_by('name')
    serializer_class = SpecialityListSerializer

class SpecialityDetailView(generics.RetrieveAPIView):
    """Get speciality details"""
    queryset = Speciality.objects.filter(is_removed=False)
    serializer_class = SpecialitySerializer
    lookup_field = 'id'

@method_decorator(ratelimit(key="ip", rate="10/h", method="POST"), name='post')
class SpecialityCreateView(generics.CreateAPIView):
    """Create new speciality (admin only)"""
    permission_classes = [IsAdminUser]
    serializer_class = SpecialityCreateSerializer
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        serializer.save()

class SpecialityUpdateView(generics.UpdateAPIView):
    """Update speciality (admin only)"""
    permission_classes = [IsAdminUser]
    queryset = Speciality.objects.filter(is_removed=False)
    serializer_class = SpecialityCreateSerializer
    parser_classes = [MultiPartParser, FormParser]
    lookup_field = 'id'

    def perform_update(self, serializer):
        try:
            speciality = SpecialityService.update_speciality(
                self.get_object(),
                name=serializer.validated_data.get('name'),
                image=serializer.validated_data.get('image')
            )
            serializer.instance = speciality
        except ValidationError as e:
            raise ValidationError({"detail": str(e)})

class SpecialityDeleteView(generics.DestroyAPIView):
    """Soft delete speciality (admin only)"""
    permission_classes = [IsAdminUser]
    queryset = Speciality.objects.filter(is_removed=False)
    lookup_field = 'id'

    def perform_destroy(self, instance):
        try:
            SpecialityService.soft_delete_speciality(instance)
        except ValidationError as e:
            raise ValidationError({"detail": str(e)})