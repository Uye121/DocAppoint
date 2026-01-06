from django.utils import timezone
from rest_framework import mixins, viewsets, permissions
from ..models import Speciality
from ..serializers import (
    SpecialitySerializer,
    SpecialityListSerializer,
    SpecialityCreateSerializer,
)
from ..permissions import IsStaffOrAdmin

class SpecialityViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    Features:
        - Authenticated user can view specialities
    """
    queryset = Speciality.objects.filter(
        is_removed=False
    )

    def get_serializer_class(self):
        if self.action == "create":
            return SpecialityCreateSerializer
        if self.action == "list":
            return SpecialityListSerializer
        return SpecialitySerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsStaffOrAdmin()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        return serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user,
        )

    def perform_update(self, serializer):
        serializer.save(
            updated_by=self.request.user
        )