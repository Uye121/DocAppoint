from rest_framework import mixins, viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django_filters.rest_framework import DjangoFilterBackend

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

    queryset = Speciality.objects.filter(is_removed=False)
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["name"]

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
        if serializer.validated_data.get("is_removed") is True:
            serializer.save(updated_by=self.request.user, removed_at=timezone.now())
        else:
            serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=["post"], url_path="restore")
    def restore(self, request, pk=None):
        """Restore a soft-deleted speciality"""
        try:
            speciality = Speciality.objects.get(pk=pk)
        except ObjectDoesNotExist:
            return Response(
                {"detail": "Speciality not found"}, status=status.HTTP_404_NOT_FOUND
            )

        if not speciality.is_removed:
            return Response(
                {"detail": "Speciality is not deleted."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        speciality.is_removed = False
        speciality.removed_at = None
        speciality.updated_by = request.user
        speciality.save(update_fields=["is_removed", "removed_at", "updated_by"])

        return Response({"detail": "Speciality restored successfully."})
