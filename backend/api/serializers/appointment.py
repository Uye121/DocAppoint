from rest_framework import serializers
from django.utils import timezone
from ..models import (
    Appointment,
    Slot,
    Patient,
    HealthcareProvider,
    Hospital,
    ProviderHospitalAssignment,
)
from .patient import PatientSerializer
from .healthcare_provider import HealthcareProviderListSerializer
from .hospital import HospitalTinySerializer
from ..mixin import CamelCaseMixin


class SlotSerializer(CamelCaseMixin, serializers.ModelSerializer):
    hospital_id = serializers.PrimaryKeyRelatedField(
        queryset=Hospital.objects.all(), write_only=True, source="hospital"
    )
    hospital_timezone = serializers.CharField(
        source="hospital.timezone", read_only=True
    )

    class Meta:
        model = Slot
        fields = [
            "id",
            "healthcare_provider",
            "hospital_id",
            "hospital_timezone",
            "start",
            "end",
            "status",
            "duration",
        ]
        read_only_fields = ["id", "duration"]

    def validate(self, attrs):
        if "start" in attrs and "end" in attrs:
            if attrs["start"] >= attrs["end"]:
                raise serializers.ValidationError(
                    {"end": "End time must be after start time."}
                )

        if "end" in attrs and attrs["end"] < timezone.now():
            raise serializers.ValidationError(
                {"end": "Cannot create/modify a slot in the past."}
            )

        if "start" in attrs and self.instance:
            if attrs["start"] >= self.instance.end:
                raise serializers.ValidationError(
                    {"start": "Start time must be before existing end time."}
                )

        if "end" in attrs and self.instance:
            if self.instance.start >= attrs["end"]:
                raise serializers.ValidationError(
                    {"end": "End time must be after existing start time."}
                )
        return attrs


class AppointmentListSerializer(CamelCaseMixin, serializers.ModelSerializer):
    patient_id = serializers.CharField(source="patient.user.id", read_only=True)
    provider_id = serializers.CharField(
        source="healthcare_provider.user.id", read_only=True
    )
    provider_image = serializers.ImageField(
        source="healthcare_provider.user.image", read_only=True
    )
    patient_name = serializers.CharField(
        source="patient.user.get_full_name", read_only=True
    )
    provider_name = serializers.CharField(
        source="healthcare_provider.user.get_full_name", read_only=True
    )
    hospital = HospitalTinySerializer(source="location", read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "patient_id",
            "provider_id",
            "patient_name",
            "provider_name",
            "provider_image",
            "appointment_start_datetime_utc",
            "appointment_end_datetime_utc",
            "hospital",
            "reason",
            "status",
        ]


class AppointmentDetailSerializer(CamelCaseMixin, serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    provider = HealthcareProviderListSerializer(
        read_only=True, source="healthcare_provider"
    )
    location = serializers.StringRelatedField()

    class Meta:
        model = Appointment
        fields = [
            "id",
            "patient",
            "provider",
            "appointment_start_datetime_utc",
            "appointment_end_datetime_utc",
            "location",
            "reason",
            "status",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate_appointment_start_datetime_utc(self, value):
        if value < timezone.now():
            raise serializers.ValidationError(
                "Cannot schedule an appointment in the past."
            )
        return value

    def validate(self, attrs):
        start = attrs.get("appointment_start_datetime_utc")
        end = attrs.get("appointment_end_datetime_utc")
        if start and end and end <= start:
            raise serializers.ValidationError(
                {"appointment_end_datetime_utc": "End must be after start."}
            )
        return attrs


class AppointmentCreateSerializer(CamelCaseMixin, serializers.ModelSerializer):
    patient = serializers.PrimaryKeyRelatedField(
        queryset=Patient.objects.all(),
        required=False,
        write_only=True,
    )
    provider = serializers.PrimaryKeyRelatedField(
        source="healthcare_provider", queryset=HealthcareProvider.objects.all()
    )
    location = serializers.PrimaryKeyRelatedField(
        queryset=Hospital.objects.filter(is_removed=False)
    )

    class Meta:
        model = Appointment
        fields = [
            "id",
            "patient",
            "provider",
            "appointment_start_datetime_utc",
            "appointment_end_datetime_utc",
            "location",
            "reason",
        ]

    def validate_appointment_start_datetime_utc(self, value):
        if value < timezone.now():
            raise serializers.ValidationError(
                "Cannot schedule an appointment in the past."
            )
        return value

    def validate(self, attrs):
        if Appointment.objects.filter(
            patient=attrs.get("patient"),
            healthcare_provider=attrs.get("healthcare_provider"),
            appointment_start_datetime_utc=attrs.get("appointment_start_datetime_utc"),
            cancelled_at__isnull=True,
        ).exists():
            raise serializers.ValidationError(
                "An appointment already exist at this time"
            )

        start = attrs.get("appointment_start_datetime_utc")
        end = attrs.get("appointment_end_datetime_utc")
        if start and end and end <= start:
            raise serializers.ValidationError(
                {"appointment_end_datetime_utc": "End must be after start."}
            )

        provider = attrs.get("healthcare_provider")
        hospital = attrs.get("location")

        # Check for provider having active assignment for the hospital
        is_active = ProviderHospitalAssignment.objects.filter(
            healthcare_provider=provider,
            hospital=hospital,
            is_active=True,
            end_datetime_utc__isnull=True,
        ).exists()

        if not is_active:
            raise serializers.ValidationError(
                {"location": "Provider is not affiliated with the hospital."}
            )

        return attrs
