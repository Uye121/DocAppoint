from rest_framework import serializers
from ..models import (
    HealthcareProvider,
    MedicalRecord,
    Hospital,
    Appointment,
    Patient,
)
from ..mixin import CamelCaseMixin


class MedicalRecordSerializer(CamelCaseMixin, serializers.ModelSerializer):
    patient_id = serializers.UUIDField(
        source="patient.user.id",
        read_only=True,
    )
    provider_id = serializers.UUIDField(
        source="healthcare_provider.user.id",
        read_only=True,
    )
    hospital_id = serializers.IntegerField(
        source="hospital.id",
        read_only=True,
    )
    appointment_id = serializers.IntegerField(
        source="appointment.id",
        read_only=True,
    )
    class Meta:
        model = MedicalRecord
        fields = [
            "id",
            "patient_id",
            "provider_id",
            "hospital_id",
            "appointment_id",
            "diagnosis",
            "notes",
            "prescriptions",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_hospital_active(self, hospital):
        if hospital and hospital.is_removed:
            raise serializers.ValidationError(
                {"hospital_id": "Selected hospital is no longer active."}
            )
        
    def validate_appointment_ownership(self, appointment, user):
        if user.is_authenticated and hasattr(user, 'provider'):
            if appointment.healthcare_provider != user.provider:
                raise serializers.ValidationError(
                    {"appointment_id": "Providers can only link their own appointments."}
                )

    def validate_provider_active(self, provider):
        if provider.is_removed:
            raise serializers.ValidationError(
                {"detail": "Provider account is no longer active."}
            )
    
    def validate_provider_hospital_affiliation(self, provider, hospital):
        if not provider.providerhospitalassignment_set.filter(
            hospital=hospital, 
            is_active=True
        ).exists():
            raise serializers.ValidationError(
                {"hospital_id": "Provider is not affiliated with this hospital or affiliation is inactive."}
            )


class MedicalRecordCreateSerializer(MedicalRecordSerializer):
    patient_id = serializers.PrimaryKeyRelatedField(
        source="patient",
        queryset=Patient.objects.all(),
        required=True
    )
    hospital_id = serializers.PrimaryKeyRelatedField(
        source="hospital",
        queryset=Hospital.objects.all(),
        required=True
    )
    appointment_id = serializers.PrimaryKeyRelatedField(
        source="appointment",
        queryset=Appointment.objects.all(),
    )
    diagnosis = serializers.CharField(required=True, allow_blank=False)
    notes = serializers.CharField(required=True, allow_blank=False)
    prescriptions = serializers.CharField(required=True, allow_blank=False)

    class Meta(MedicalRecordSerializer.Meta):
        fields = [
            "patient_id",
            "hospital_id",
            "appointment_id",
            "diagnosis",
            "notes",
            "prescriptions",
        ]

    def validate(self, attrs):
        patient = attrs.get("patient")
        hospital = attrs.get("hospital")
        appointment = attrs.get("appointment")
        request = self.context.get("request")

        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError(
                {"detail": "Authentication required."}
            )

        self.validate_hospital_active(hospital)

        try:
            provider = request.user.provider
        except HealthcareProvider.DoesNotExist:
            raise serializers.ValidationError(
                {"detail": "Only healthcare providers can create medical records."}
            )
        
        self.validate_provider_active(provider)
        self.validate_provider_hospital_affiliation(provider, hospital)

        if appointment:
            if hasattr(appointment, 'medical_record') and appointment.medical_record:
                raise serializers.ValidationError(
                    {"appointment_id": "This appointment is already linked to another medical record."}
                )
            
            if patient and appointment.patient != patient:
                raise serializers.ValidationError(
                    {"appointment_id": "Appointment patient does not match medical record patient."}
                )

            self.validate_appointment_ownership(appointment, request.user)

        if patient and patient.user == provider.user:
            raise serializers.ValidationError(
                {"patient": "Provider cannot create medical records for themselves."}
            )

        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['healthcare_provider'] = request.user.provider
        validated_data['created_by'] = request.user
        validated_data['updated_by'] = request.user
        
        return MedicalRecord.objects.create(**validated_data)


class MedicalRecordUpdateSerializer(MedicalRecordSerializer):
    patient_id = serializers.PrimaryKeyRelatedField(
        source="patient",
        queryset=Patient.objects.all(),
        required=False
    )
    hospital_id = serializers.PrimaryKeyRelatedField(
        source="hospital",
        queryset=Hospital.objects.all(),
        required=False
    )
    appointment_id = serializers.PrimaryKeyRelatedField(
        source="appointment",
        queryset=Appointment.objects.all(),
        required=False,
    )
    diagnosis = serializers.CharField(required=False, allow_blank=False)
    notes = serializers.CharField(required=False, allow_blank=False)
    prescriptions = serializers.CharField(required=False, allow_blank=False)
    hospital_id = serializers.PrimaryKeyRelatedField(
        source="hospital",
        queryset=Hospital.objects.all(),
        required=False,
    )

    class Meta(MedicalRecordSerializer.Meta):
        fields = [
            "patient_id",
            "appointment_id",
            "hospital_id",
            "diagnosis",
            "notes",
            "prescriptions",
        ]

    def validate(self, attrs):
        request = self.context.get("request")
        instance = self.instance

        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError(
                {"detail": "Authentication required."}
            )
        
        try:
            provider = request.user.provider
        except HealthcareProvider.DoesNotExist:
            raise serializers.ValidationError(
                {"detail": "Only healthcare providers can update medical records."}
            )
        
        patient = attrs.get("patient", instance.patient)
        hospital = attrs.get("hospital", instance.hospital)
        appointment = attrs.get("appointment", instance.appointment)

        if "hospital" in attrs:
            self.validate_hospital_active(hospital)
            self.validate_provider_hospital_affiliation(provider, hospital)

        if "appointment" in attrs:
            if appointment:
                if hasattr(appointment, 'medical_record') and appointment.medical_record:
                    if appointment.medical_record != instance:
                        raise serializers.ValidationError(
                            {"appointment_id": "This appointment is already linked to another medical record."}
                        )
            
                if patient and appointment.patient != patient:
                    raise serializers.ValidationError(
                        {"appointment_id": "Appointment patient does not match medical record patient."}
                    )
                
                self.validate_appointment_ownership(appointment, request.user)

        # Check provider not updating record for themselves
        if patient and patient.user == provider.user:
            raise serializers.ValidationError(
                {"patient_id": "Provider cannot update medical records for themselves."}
            )

        return attrs

    def update(self, instance, validated_data):
        request = self.context.get("request")
        instance.updated_by = request.user

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class MedicalRecordListSerializer(MedicalRecordSerializer):
    patient_id = serializers.UUIDField(source="patient.user.id", read_only=True)
    patient_name = serializers.CharField(
        source='patient.user.get_full_name', 
        read_only=True
    )
    provider_id = serializers.UUIDField(
        source="healthcare_provider.user.id", read_only=True
    )
    provider_name = serializers.CharField(
        source='healthcare_provider.user.get_full_name', 
        read_only=True
    )
    hospital_id = serializers.UUIDField(source="hospital.id", read_only=True)
    hospital_name = serializers.CharField(
        source="hospital.name",
        read_only=True,
    )
    appointment_id = serializers.UUIDField(source="appointment.id", read_only=True)

    class Meta(MedicalRecordSerializer.Meta):
        fields = [
            'id',
            'patient_id',
            'patient_name',
            'provider_id',
            'provider_name',
            'hospital_id',
            "hospital_name",
            'appointment_id',
            'diagnosis',
            'created_at',
            'updated_at'
        ]
        read_only_fields = fields


class MedicalRecordDetailSerializer(MedicalRecordSerializer):
    patient_details = serializers.SerializerMethodField()
    provider_details = serializers.SerializerMethodField()
    hospital_details = serializers.SerializerMethodField()
    appointment_details = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(
        source='created_by.get_full_name', 
        read_only=True,
        default='System'
    )
    updated_by_name = serializers.CharField(
        source='updated_by.get_full_name', 
        read_only=True,
        default='System'
    )

    class Meta(MedicalRecordSerializer.Meta):
        fields = [
            'id',
            'patient_details',
            'provider_details',
            'hospital_details',
            'appointment_details',
            'diagnosis',
            'notes',
            'prescriptions',
            'created_at',
            'updated_at',
            'created_by', 
            'created_by_name',
            'updated_by',
            'updated_by_name',
            'is_removed',
            'removed_at'
        ]
        read_only_fields = fields

    def get_patient_details(self, obj):
        patient = obj.patient
        user = patient.user

        image_url = None
        if user.image and hasattr(user.image, 'url'):
            try:
                image_url = user.image
            except ValueError:
                image_url = None

        return {
            'id': user.id,
            'blood_type': patient.blood_type,
            'allergies': patient.allergies,
            'chronic_conditions': patient.chronic_conditions,
            'current_medications': patient.current_medications,
            'insurance': patient.insurance,
            'weight': patient.weight,
            'height': patient.height,
            'full_name': user.get_full_name(),
            'date_of_birth': user.date_of_birth,
            'image': image_url,
        }

    def get_provider_details(self, obj):
        provider = obj.healthcare_provider
        return {
            'id': provider.user.id,
            'speciality_name': provider.speciality.name,
            'license_number': provider.license_number,
            'full_name': provider.user.get_full_name(),
        }
    
    def get_hospital_details(self, obj):
        if obj.hospital:
            return {
                'id': obj.hospital.id,
                'name': obj.hospital.name,
                'phone_number': obj.hospital.phone_number,
                'timezone': obj.hospital.timezone,
            }
        return None
    
    def get_appointment_details(self, obj):
        if obj.appointment:
            appointment = obj.appointment
            return {
                'start_datetime_utc': appointment.appointment_start_datetime_utc,
                'end_datetime_utc': appointment.appointment_end_datetime_utc,
                'reason': appointment.reason,
                'status': appointment.status,
            }
