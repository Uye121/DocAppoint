from rest_framework import serializers
from ..models import (
    HealthcareProvider,
    MedicalRecord
)
from ..mixin import CamelCaseMixin


class MedicalRecordSerializer(CamelCaseMixin, serializers.ModelSerializer):
    provider_id = serializers.CharField(
        source="healthcare_provider.user.id",
        read_only=True
    )
    class Meta:
        model = MedicalRecord
        fields = [
            "id",
            "patient",
            "provider_id",
            "hospital",
            "diagnosis",
            "notes",
            "prescriptions"
        ]

    def validate(self, attrs):
        request = self.context.get("request")

        if request and request.method in ["POST", "PUT", "PATCH"]:
            patient = attrs.get("patient") or getattr(self.instance, "patient", None)

            hospital = attrs.get("hospital")
            if hospital and hospital.is_removed:
                raise serializers.ValidationError(
                    {"hospital": "Selected hospital is no longer active."}
                )

            if self.instance:
                provider = self.instance.healthcare_provider
            else:
                provider = None
            
            if patient and provider and patient.user == provider.user:
                raise serializers.ValidationError(
                    {"provider": "A Provider cannot create medical records for themselves"}
                )
        return attrs


class MedicalRecordCreateSerializer(MedicalRecordSerializer):
    class Meta(MedicalRecordSerializer.Meta):
        fields = [
            "patient",
            "hospital",
            "diagnosis",
            "notes",
            "prescriptions",
        ]

    def validate(self, attrs):
        attrs = super().validate(attrs)

        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError(
                {"detail": "Authentication required."}
            )
        
        try:
            provider = request.user.provider
            if provider.is_removed:
                raise serializers.ValidationError(
                    {"detail": "Provider account is no longer active."}
                )
            
            hospital = attrs.get("hospital")
            if hospital:
                if not provider.hospitals.filter(id=hospital.id).exists():
                    raise serializers.ValidationError(
                        {"hospital": "Provider is not affiliated with this hospital."}
                    )
            

            patient = attrs.get("patient")
            if patient and patient.user == provider.user:
                raise serializers.ValidationError(
                    {"patient": "Provider cannot create medical records for themselves."}
                )
        except HealthcareProvider.DoesNotExist:
            raise serializers.ValidationError(
                {"detail": "Only healthcare providers can create medical records."}
            )
        

        return attrs

    def create(self, validated_data):
        request = self.context.get('request')

        validated_data['healthcare_provider'] = request.user.provider
        
        validated_data['created_by'] = request.user
        validated_data['updated_by'] = request.user
        
        return MedicalRecord.objects.create(**validated_data)


class MedicalRecordUpdateSerializer(MedicalRecordSerializer):
    class Meta(MedicalRecordSerializer.Meta):
        fields = [
            "diagnosis",
            "notes",
            "prescriptions",
            "hospital"
        ]

    def validate(self, attrs):
        attrs = super().validate(attrs)

        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError(
                {"detail": "Authentication required."}
            )
        
        if 'hospital' in attrs:
            hospital = attrs['hospital']
            if hospital.is_removed:
                raise serializers.ValidationError(
                    {"hospital": "Selected hospital is no longer active."}
                )
            
            # Check if provider is affiliated with the new hospital
            if not self.instance.healthcare_provider.hospitals.filter(id=hospital.id).exists():
                raise serializers.ValidationError(
                    {"hospital": "Provider is not affiliated with this hospital."}
                )
    
        return attrs

    def update(self, instance, validated_data):
        request = self.context.get("request")

        if request and request.user.is_authenticated:
            instance.updated_by = request.user

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class MedicalRecordListSerializer(MedicalRecordSerializer):
    patient_id = serializers.CharField(source="patient.user.id", read_only=True)
    provider_id = serializers.CharField(
        source="healthcare_provider.user.id", read_only=True
    )
    patient_name = serializers.CharField(
        source='patient.user.get_full_name', 
        read_only=True
    )
    provider_name = serializers.CharField(
        source='healthcare_provider.user.get_full_name', 
        read_only=True
    )
    hospital_name = serializers.CharField(
        source="hospital.name",
        read_only=True,
    )

    class Meta(MedicalRecordSerializer.Meta):
        fields = [
            'id',
            'patient_id',
            'patient_name',
            'provider_id',
            'provider_name',
            "hospital_name",
            'diagnosis',
            'created_at',
            'updated_at'
        ]
        read_only_fields = fields


class MedicalRecordDetailSerializer(MedicalRecordSerializer):
    patient_details = serializers.SerializerMethodField()
    provider_details = serializers.SerializerMethodField()
    hospital_details = serializers.SerializerMethodField()
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
        return {
            'id': patient.user.id,
            'blood_type': patient.blood_type,
            'allergies': patient.allergies,
            'chronic_conditions': patient.chronic_conditions,
            'current_medications': patient.current_medications,
            'insurance': patient.insurance,
            'weight': patient.weight,
            'height': patient.height,
            'full_name': patient.user.get_full_name(),
            'date_of_birth': patient.user.date_of_birth,
            'image': patient.user.image,
        }

    def get_provider_details(self, obj):
        provider = obj.healthcare_provider
        return {
            'id': provider.user.id,
            'speciality_name': provider.speciality.name,
            'license_number': provider.license_number,
            'full_name': provider.user.get_full_name(),
        }
    
    def get_hospital_info(self, obj):
        if obj.hospital:
            return {
                'id': obj.hospital.id,
                'name': obj.hospital.name,
                'phone_number': obj.hospital.phone_number,
                'timezone': obj.hospital.timezone,
            }
        return None
