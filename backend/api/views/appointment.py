from datetime import timedelta
from rest_framework import viewsets, serializers, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_time
from django.db.models import F

from ..models import Appointment, Slot, HealthcareProvider
from ..serializers import (
    AppointmentListSerializer,
    AppointmentDetailSerializer,
    AppointmentCreateSerializer,
    SlotSerializer
)
from ..services.appointment import refresh_slot_status, generate_daily_slots

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
        
    @action(detail=True, methods=["post"], url_path="confirm")
    def confirm(self, request, pk=None):
        appointment = self.get_object()
        if appointment.status != Appointment.Status.REQUESTED:
            return Response(
                {"detail": "Only requested appointments can be confirmed."},
                status=status.HTTP_400_BAD_REQUEST
            )
        appointment.status = Appointment.Status.CONFIRMED
        appointment.save(update_fields=["status"])

        refresh_slot_status(
            appointment.healthcare_provider,
            appointment.location.hospital,
            appointment.appointment_start_datetime_utc,
            appointment.appointment_end_datetime_utc,
        )
        return Response({"detail": "Appointment confirmed."})
    
    @action(detail=False, methods=["post"], url_path="generate-slots")
    def generate_slots(self, request):
        provider_id = request.data.get("provider")
        date_str = request.data.get("date")
        duration = int(request.data.get("duration", 30))
        opening_str = request.data.get("opening", "9:00")
        closing_str = request.data.get("closing", "17:00")

        if not (provider_id and date_str):
            return Response(
                {"detail": "Provider and date are required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            opening = parse_time(opening_str)
            closing = parse_time(closing_str)
        except ValueError:
            return Response(
                {"detail": "opening / closing must be HH:MM (24-hour)."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not opening or not closing:
            return Response(
                {"detail": "Invalid opening and closing."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if opening >= closing:
            return Response(
                {"detail": "closing must be after opening."},
                status=status.HTTP_400_BAD_REQUEST
            )

        provider = get_object_or_404(HealthcareProvider, pk=provider_id)
        hospital = provider.primary_hospital
        date = timezone.datetime.strptime(date_str, "%Y-%m-%d").date()

        generate_daily_slots(
            provider,
            hospital,
            date,
            duration_min=duration,
            opening=opening,
            closing=closing
        )
        return Response({"detail": "Slots generated."}, status=status.HTTP_201_CREATED)
        
class SlotViewSet(viewsets.ModelViewSet):
    queryset = Slot.objects.select_related("healthcare_provider__user", "hospital").all()
    serializer_class = SlotSerializer

    def get_queryset(self):
        """Providers see only their own slots; staff sees all."""
        user = self.request.user
        if hasattr(user, "provider"):
            return self.queryset.filter(healthcare_provider=user.provider)
        return self.queryset.all()
    
    def get_permissions(self):
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        """Force the slot to belong to the calling provider (or allow staff to pick)."""
        user = self.request.user
        if hasattr(user, "provider"):
            serializer.save(healthcare_provider=user.provider)
        else:
            # staff/admin must supply provider in payload
            serializer.save()

    @action(detail=False, methods=["get"], url_path="range")
    def range(self, request):
        provider_id = request.query_params.get("provider")
        start_str = request.query_params.get("start_date")
        end_str = request.query_params.get("end_date")

        if not provider_id:
            return Response(
                {"detail": "provider required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Use this week by default (Mon to Sun)
        if not (start_str and end_str):
            today = timezone.now().date()
            start_date = today - timedelta(days=today.weekday())
            start_date, end_date = today, start_date + timedelta(days=6)
        else:
            try:
                start_date = timezone.datetime.strptime(start_str, "%Y-%m-%d").date()
                end_date   = timezone.datetime.strptime(end_str, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"detail": "Dates must be YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if end_date < start_date:
                return Response(
                    {"detail": "end_date must be >= start_date."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        slots = (self.get_queryset()
                .filter(healthcare_provider_id=provider_id,
                        start__date__range=[start_date, end_date])
                .order_by("start")
                .values("id", "start", "end", hospital_name=F("hospital__name")))

        grouped_slots = {}
        for slot in slots:
            day = slot["start"].date().isoformat()
            grouped_slots.setdefault(day, []).append(slot)
        return Response(grouped_slots)

    @action(detail=False, methods=["get"], url_path="free")
    def free(self, request):
        self.filter_backends = [DjangoFilterBackend]
        self.filterset_fields = ["healthcare_provider", "hospital", "status"]
        qs = self.get_queryset().filter(
            status=Slot.Status.FREE,
            start__date=request.query_params.get("date"),
        )
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)