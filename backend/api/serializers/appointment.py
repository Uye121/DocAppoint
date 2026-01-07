from rest_framework import serializers
from django.utils import timezone
from ..models import Appointment, Slot, Patient, HealthcareProvider, ProviderHospitalAssignment
from .patient import PatientSerializer
from .healthcare_provider import HealthcareProviderListSerializer

class SlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Slot
        fields = [
            "id",
            "provider",
            "hospital",
            "start",
            "end",
            "status",
            "duration",
        ]
        read_only_fields = ["id", "duration"]

    def validate(self, attrs):
        if attrs["start"] >= attrs["end"]:
            raise serializers.ValidationError(
                {"end": "End time must be after start time."}
            )
        if attrs["end"] < timezone.now():
            raise serializers.ValidationError(
                {"end": "Cannot create/modify a slot in the past."}
            )
        return attrs

class AppointmentListSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    healthcare_provider = HealthcareProviderListSerializer(read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "patient",
            "healthcare_provider",
            "appointment_start_datetime_utc",
            "appointment_end_datetime_utc",
            "location",
            "reason",
            "status",
        ]

class AppointmentDetailSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    healthcare_provider = HealthcareProviderListSerializer(read_only=True)
    location = serializers.StringRelatedField()  # or nested if you want

    class Meta:
        model = Appointment
        fields = [
            "id",
            "patient",
            "healthcare_provider",
            "appointment_start_datetime_utc",
            "appointment_end_datetime_utc",
            "location",
            "reason",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate_appointment_start_datetime_utc(self, value):
        if value < timezone.now():
            raise serializers.ValidationError("Cannot schedule an appointment in the past.")
        return value

    def validate(self, attrs):
        start = attrs.get("appointment_start_datetime_utc")
        end = attrs.get("appointment_end_datetime_utc")
        if start and end and end <= start:
            raise serializers.ValidationError(
                {"appointment_end_datetime_utc": "End must be after start."}
            )
        return attrs

class AppointmentCreateSerializer(serializers.ModelSerializer):
    patient = serializers.PrimaryKeyRelatedField(
        queryset=Patient.objects.all(),
        required=False,
        write_only=True,
    )
    healthcare_provider = serializers.PrimaryKeyRelatedField(
        queryset=HealthcareProvider.objects.all()
    )
    location = serializers.PrimaryKeyRelatedField(
        queryset=ProviderHospitalAssignment.objects.all()
    )

    class Meta:
        model = Appointment
        fields = [
            "patient",
            "healthcare_provider",
            "appointment_start_datetime_utc",
            "appointment_end_datetime_utc",
            "location",
            "reason",
        ]

    def validate_appointment_start_datetime_utc(self, value):
        if value < timezone.now():
            raise serializers.ValidationError("Cannot schedule an appointment in the past.")
        return value

    def validate(self, attrs):
        start = attrs.get("appointment_start_datetime_utc")
        end = attrs.get("appointment_end_datetime_utc")
        if start and end and end <= start:
            raise serializers.ValidationError(
                {"appointment_end_datetime_utc": "End must be after start."}
            )
        return attrs