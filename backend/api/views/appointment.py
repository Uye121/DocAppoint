from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django.db.models import F
from django.utils.dateparse import parse_time
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, serializers, permissions, status
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from django.core.exceptions import ObjectDoesNotExist

from ..models import Appointment, Slot, HealthcareProvider
from ..serializers import (
    AppointmentListSerializer,
    AppointmentDetailSerializer,
    AppointmentCreateSerializer,
    SlotSerializer
)
from ..services.appointment import generate_daily_slots

class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.select_related(
        "patient__user", "healthcare_provider__user", "location"
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

        with transaction.atomic():
            if hasattr(user, "patient"):
                appointment = serializer.save(patient=user.patient)
            elif hasattr(user, "provider"):
                if not serializer.validated_data.get("patient"):
                    raise serializers.ValidationError(
                        {"patient": "Required when booking appointment for patient."}
                    )
                appointment = serializer.save()
            else:
                raise PermissionDenied("Only patients or providers can schedule appointments.")

            slot = (
                Slot.objects.select_for_update()
                    .filter(
                        healthcare_provider=appointment.healthcare_provider,
                        hospital=appointment.location,
                        start__lte=appointment.appointment_start_datetime_utc,
                        end__gte=appointment.appointment_end_datetime_utc,
                        status=Slot.Status.FREE,
                    )
                    .first()
            )

            if not slot:
                raise serializers.ValidationError(
                    {"detail": "No available slot for the requested time."}
                )
        
            slot.appointment = appointment
            slot.status = Slot.Status.BOOKED
            slot.save(update_fields=["appointment", "status"])
        return appointment
        
    @action(detail=True, methods=["post"], url_path="set-status")
    def set_status(self, request, pk=None):
        appointment = self.get_object()
        new_status = request.data.get("status", Appointment.Status.CONFIRMED).upper()

        allowed = {
            Appointment.Status.REQUESTED: {
                Appointment.Status.CONFIRMED,
                Appointment.Status.CANCELLED,
            },
            Appointment.Status.CONFIRMED: {
                Appointment.Status.CANCELLED,
                Appointment.Status.RESCHEDULED,
            }
        }

        # Reject not allowed status change
        if new_status not in allowed.get(appointment.status, set()):
            return Response(
                {"detail": "Prohibited status change."},
                status=status.HTTP_400_BAD_REQUEST
            )
        appointment.status = new_status
        
        if new_status == Appointment.Status.RESCHEDULED:
            new_start = request.data.get("new_start_datetime_utc")
            new_end = request.data.get("new_end_datetime_utc")

            if not new_start or not new_end:
                return Response(
                    {"detail": "New start and end times are required for rescheduling."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            with transaction.atomic():
                # Check for available slots
                slots = Slot.objects.select_for_update().filter(
                    healthcare_provider=appointment.healthcare_provider,
                    hospital=appointment.location,
                    start__lt=new_end,
                    end__gt=new_start,
                    status=Slot.Status.FREE,
                ).order_by('start')

                if not slots.exists():
                    return Response({"detail": "No available slot for the requested time."}, status=status.HTTP_400_BAD_REQUEST)

                coverage_start = slots.first().start if slots else None
                coverage_end   = slots.last().end   if slots else None
                if not (coverage_start <= new_start and coverage_end >= new_end):
                    return Response({"detail": "No continuous free block for the requested time."}, status=400)

                slots.update(status=Slot.Status.BOOKED)
            
                # Release old slots
                old_start = appointment.appointment_start_datetime_utc
                old_end = appointment.appointment_end_datetime_utc
                Slot.objects.filter(
                    healthcare_provider=appointment.healthcare_provider,
                    hospital=appointment.location,
                    start__lt=old_end,
                    end__gt=old_start,
                    status=Slot.Status.BOOKED,
                ).update(status=Slot.Status.FREE)

            appointment.appointment_start_datetime_utc = new_start
            appointment.appointment_end_datetime_utc = new_end
        elif new_status == Appointment.Status.CANCELLED:
            appointment.cancelled_at = timezone.now()
            Slot.objects.filter(
                healthcare_provider=appointment.healthcare_provider,
                hospital=appointment.location,
                start__lt=appointment.appointment_end_datetime_utc,
                end__gt=appointment.appointment_start_datetime_utc,
                status=Slot.Status.BOOKED,
            ).update(status=Slot.Status.FREE)
        elif new_status == Appointment.Status.CONFIRMED:
            Slot.objects.filter(
                healthcare_provider=appointment.healthcare_provider,
                hospital=appointment.location,
                start__lt=appointment.appointment_end_datetime_utc,
                end__gt=appointment.appointment_start_datetime_utc,
                status=Slot.Status.FREE,
            ).update(status=Slot.Status.BOOKED)

        # save status (and new times if rescheduled)
        appointment.save(update_fields=[
            "status",
            "cancelled_at",
            "appointment_start_datetime_utc",
            "appointment_end_datetime_utc",
        ])
        return Response({"detail": f"Appointment {new_status.lower()}."})
    
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
            end_date = start_date + timedelta(days=6)
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
                .values("id", "start", "end", "status",
                        hospitalId=F("hospital_id"),
                        hospitalName=F("hospital__name"),
                        hospitalTimezone=F("hospital__timezone"))
                )

        grouped_slots = {}
        for slot in slots:
            day = slot["start"].date().isoformat()
            grouped_slots.setdefault(day, []).append(slot)
        return Response(grouped_slots)

    @action(detail=False, methods=["get"], url_path="free")
    def free(self, request):
        provider_id = request.query_params.get("provider")
        date_str = request.query_params.get("date")
        if not (provider_id and date_str):
            return Response(
                {"detail": "provider and date required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        slots = (self.get_queryset()
                 .filter(healthcare_provider_id=provider_id,
                         start__date=date_str,
                         status=Slot.Status.FREE)
                 .order_by("start"))
        serializer = self.get_serializer(slots, many=True)
        return Response(serializer.data)
