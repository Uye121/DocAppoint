# appointments/views.py
from rest_framework import viewsets, serializers, permissions
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.decorators import action

from ..models import Appointment, Slot
from ..serializers import (
    AppointmentListSerializer,
    AppointmentDetailSerializer,
    AppointmentCreateSerializer,
    SlotSerializer
)

class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.select_related(
        "patient__user", "healthcare_provider__user", "location__hospital"
    )

    def get_serializer_class(self):
        if self.action == "list":
            return AppointmentListSerializer
        if self.action in ("create",):
            return AppointmentCreateSerializer
        return AppointmentDetailSerializer

    def get_queryset(self):
        """Users can only see their own appointments"""
        user = self.request.user
        if hasattr(user, "patient"):
            return self.queryset.filter(patient=user.patient)
        if hasattr(user, "provider"):
            return self.queryset.filter(healthcare_provider=user.provider)
        # staff / admin see everything
        return self.queryset.all()

    def get_permissions(self):
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        user = self.request.user

        if hasattr(user, "patient"):
            serializer.save(patient=user.patient)

        elif hasattr(user, "provider"):
            # provider books on behalf of a patient – patient id required
            if not serializer.validated_data.get("patient"):
                raise serializers.ValidationError(
                    {"patient": "Required when booking appointment for patient."}
                )
            serializer.save()

        else:
            raise PermissionDenied("Only patients or providers can schedule appointments.")
        
class SlotViewSet(viewsets.ModelViewSet):
    queryset = Slot.objects.select_related("provider__user", "hospital").all()
    serializer_class = SlotSerializer

    def get_queryset(self):
        """Providers see only their own slots; staff sees all."""
        user = self.request.user
        if hasattr(user, "provider"):
            return self.queryset.filter(provider=user.provider)
        return self.queryset.all()
    
    def get_permissions(self):
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        """Force the slot to belong to the calling provider (or allow staff to pick)."""
        user = self.request.user
        if hasattr(user, "provider"):
            serializer.save(provider=user.provider)
        else:
            # staff/admin must supply provider in payload
            serializer.save()

    @action(detail=False, methods=["get"], url_path="free")
    def free(self, request):
        self.filter_backends = [DjangoFilterBackend]
        self.filterset_fields = ["provider", "hospital", "status"]
        qs = self.get_queryset().filter(
            status=Slot.Status.FREE,
            start__date=request.query_params.get("date"),
        )
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)