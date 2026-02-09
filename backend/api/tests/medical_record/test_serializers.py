import re
import pytest
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APIRequestFactory
from django.utils import timezone
from rest_framework.exceptions import ValidationError as DRFValidationError

from api.models import ProviderHospitalAssignment
from api.serializers import (
    MedicalRecordSerializer,
    MedicalRecordCreateSerializer,
    MedicalRecordUpdateSerializer,
    MedicalRecordListSerializer,
    MedicalRecordDetailSerializer,
)

pytestmark = pytest.mark.django_db

class TestMedicalRecordSerializer:
    
    def test_serializer_fields(self, medical_record_factory):
        record = medical_record_factory()
        serializer = MedicalRecordSerializer(record)
        
        expected_fields = [
            'id',
            'patient',
            'providerId',
            'hospital',
            'diagnosis',
            'notes',
            'prescriptions'
        ]
        
        assert set(serializer.data.keys()) == set(expected_fields)

    def test_validate_provider_cannot_create_record_for_self(self, patient_factory, healthcare_provider_factory):
        provider = healthcare_provider_factory()
        patient = patient_factory()
        
        # Make patient user same as provider user
        patient.user = provider.user
        patient.save()
        
        data = {
            'patient': patient.user.id,
            'diagnosis': 'Test diagnosis',
            'notes': 'Test notes',
            'prescriptions': 'Test prescriptions'
        }
        
        serializer = MedicalRecordSerializer(data=data, context={'request': None})
        
        with pytest.raises(Exception):
            serializer.is_valid(raise_exception=True)

class TestMedicalRecordCreateSerializer:
    def assign_provider_to_hospital(self, provider, hospital):
        ProviderHospitalAssignment.objects.filter(
            healthcare_provider=provider,
            hospital=hospital,
            is_active=True,
            end_datetime_utc__isnull=True
        ).update(is_active=False, end_datetime_utc=timezone.now())
        
        # Create new assignment
        ProviderHospitalAssignment.objects.create(
            healthcare_provider=provider,
            hospital=hospital,
            is_active=True,
            start_datetime_utc=timezone.now(),
            created_by=provider.user,
            updated_by=provider.user
        )
    def test_create_serializer_fields(self):
        serializer = MedicalRecordCreateSerializer()
        
        expected_fields = [
            'patient',
            'hospital',
            'diagnosis',
            'notes',
            'prescriptions',
        ]
        
        assert set(serializer.fields.keys()) == set(expected_fields)
    
    def test_validate_authentication_required(self, patient_factory, hospital_factory):
        patient = patient_factory()
        hospital = hospital_factory()

        data = {
            'patient': patient.user.id,
            'hospital': hospital.id,
            'diagnosis': 'Test',
            'notes': 'Test',
            'prescriptions': 'Test'
        }
        
        serializer = MedicalRecordCreateSerializer(data=data, context={'request': None})
        
        with pytest.raises(Exception) as exc_info:
            serializer.is_valid(raise_exception=True)
        error_message = str(exc_info.value)
        assert 'Authentication required' in error_message or 'detail' in serializer.errors

    def test_validate_non_provider_user(self, patient_factory, hospital_factory):
        factory = APIRequestFactory()
        request = factory.post('/')
        patient = patient_factory()
        hospital = hospital_factory()
        request.user = patient.user
        
        data = {
            'patient': patient.user.id,
            'hospital': hospital.id,
            'diagnosis': 'Test',
            'notes': 'Test',
            'prescriptions': 'Test'
        }
        
        serializer = MedicalRecordCreateSerializer(data=data, context={'request': request})
        
        with pytest.raises(Exception) as exc_info:
            serializer.is_valid(raise_exception=True)
        assert 'Only healthcare providers' in str(exc_info.value)
    
    def test_validate_provider_removed(self, provider_factory, patient_factory, hospital_factory):
        provider = provider_factory(is_removed=True, removed_at=timezone.now())
        patient = patient_factory()
        hospital = hospital_factory()
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = provider.user
        
        data = {
            'patient': patient.user.id,
            'hospital': hospital.id,
            'diagnosis': 'Test',
            'notes': 'Test',
            'prescriptions': 'Test'
        }
        
        serializer = MedicalRecordCreateSerializer(data=data, context={'request': request})
        
        with pytest.raises(Exception) as exc_info:
            serializer.is_valid(raise_exception=True)
        assert 'Provider account is no longer active' in str(exc_info.value)

    def test_validate_hospital_not_affiliated(
        self, provider_factory, patient_factory, hospital_factory
    ):
        provider = provider_factory()
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = provider.user
        
        patient = patient_factory()
        hospital = hospital_factory()  
        
        data = {
            'patient': patient.user.id,
            'hospital': hospital.id,
            'diagnosis': 'Test diagnosis',
            'notes': 'Test notes',
            'prescriptions': 'Test prescriptions'
        }
        
        serializer = MedicalRecordCreateSerializer(data=data, context={'request': request})
        
        with pytest.raises(Exception) as exc_info:
            serializer.is_valid(raise_exception=True)
        assert 'Provider is not affiliated with this hospital' in str(exc_info.value)

    def test_validate_provider_cannot_create_for_self(
        self, provider_factory, hospital_factory, patient_factory
    ):
        provider = provider_factory()
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = provider.user
        
        patient = patient_factory(user=provider.user)
        
        # Make provider affiliated with hospital
        hospital = hospital_factory()
        ProviderHospitalAssignment.objects.create(
            healthcare_provider=provider,
            hospital=hospital,
            is_active=True,
            created_by=provider.user,
            updated_by=provider.user
        )
        
        data = {
            'patient': patient.user.id,
            'hospital': hospital.id,
            'diagnosis': 'Test diagnosis',
            'notes': 'Test notes',
            'prescriptions': 'Test prescriptions'
        }
        
        serializer = MedicalRecordCreateSerializer(data=data, context={'request': request})
        
        with pytest.raises(Exception) as exc_info:
            serializer.is_valid(raise_exception=True)
        assert 'Provider cannot create medical records for themselves' in str(exc_info.value)

    def test_validate_removed_hospital(
        self, provider_factory, patient_factory, hospital_factory
    ):
        provider = provider_factory()
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = provider.user
        
        patient = patient_factory()
        hospital = hospital_factory(is_removed=True, removed_at=timezone.now())
        
        ProviderHospitalAssignment.objects.create(
            healthcare_provider=provider,
            hospital=hospital,
            is_active=True,
            created_by=provider.user,
            updated_by=provider.user
        )
        
        data = {
            'patient': patient.user.id,
            'hospital': hospital.id,
            'diagnosis': 'Test diagnosis',
            'notes': 'Test notes',
            'prescriptions': 'Test prescriptions'
        }
        
        serializer = MedicalRecordCreateSerializer(data=data, context={'request': request})
        
        with pytest.raises(Exception) as exc_info:
            serializer.is_valid(raise_exception=True)
        assert 'Selected hospital is no longer active' in str(exc_info.value)

    def test_create_medical_record_success(
        self, provider_factory, patient_factory, hospital_factory
    ):
        provider = provider_factory()
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = provider.user
        
        patient = patient_factory()
        hospital = hospital_factory()
        
        # Create proper affiliation with audit fields
        from api.models import ProviderHospitalAssignment
        ProviderHospitalAssignment.objects.create(
            healthcare_provider=provider,
            hospital=hospital,
            is_active=True,
            created_by=provider.user,
            updated_by=provider.user
        )
        
        data = {
            'patient': patient.user.id,
            'hospital': hospital.id,
            'diagnosis': 'Test diagnosis',
            'notes': 'Test notes',
            'prescriptions': 'Test prescriptions'
        }
        
        serializer = MedicalRecordCreateSerializer(
            data=data, 
            context={'request': request}
        )
        
        assert serializer.is_valid() is True
        
        record = serializer.save()
        
        assert record.patient == patient
        assert record.hospital == hospital
        assert record.healthcare_provider == provider
        assert record.diagnosis == 'Test diagnosis'
        assert record.created_by == provider.user
        assert record.updated_by == provider.user

    def test_create_medical_record_with_medical_record_factory(
        self, medical_record_factory
    ):
        record = medical_record_factory()
        provider = record.healthcare_provider
        
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = provider.user
        
        # Create new data based on existing record
        data = {
            'patient': record.patient.user.id,
            'hospital': record.hospital.id,
            'diagnosis': 'New diagnosis',
            'notes': 'New notes',
            'prescriptions': 'New prescriptions'
        }
        
        serializer = MedicalRecordCreateSerializer(
            data=data, 
            context={'request': request}
        )
        
        assert serializer.is_valid() is True

    def test_validate_missing_required_fields(
        self, provider_factory, patient_factory, hospital_factory
    ):
        provider = provider_factory()
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = provider.user
        
        patient = patient_factory()
        hospital = hospital_factory()
        
        # Create affiliation
        from api.models import ProviderHospitalAssignment
        ProviderHospitalAssignment.objects.create(
            healthcare_provider=provider,
            hospital=hospital,
            is_active=True,
            created_by=provider.user,
            updated_by=provider.user
        )
        
        # Test missing diagnosis
        data = {
            'patient': patient.user.id,
            'hospital': hospital.id,
            'notes': 'Test notes',
            'prescriptions': 'Test prescriptions'
        }
        
        serializer = MedicalRecordCreateSerializer(data=data, context={'request': request})
        assert serializer.is_valid() is False
        assert 'diagnosis' in serializer.errors

    def test_create_with_provider_primary_hospital(
        self, provider_factory, patient_factory, hospital_factory
    ):
        hospital = hospital_factory(
            name="Primary Hospital",
            address_line1="123 Main St",
            phone_number="555-1234",
            timezone="UTC"
        )
        
        provider = provider_factory(primary_hospital=hospital)
        
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = provider.user
        
        patient = patient_factory()
        
        data = {
            'patient': patient.user.id,
            'hospital': hospital.id,
            'diagnosis': 'Test diagnosis',
            'notes': 'Test notes',
            'prescriptions': 'Test prescriptions'
        }
        
        serializer = MedicalRecordCreateSerializer(data=data, context={'request': request})
        
        assert serializer.is_valid() is True
        
        record = serializer.save()
        
        assert record.hospital == hospital
        assert record.healthcare_provider == provider

    def test_create_with_multiple_hospital_affiliations(
        self, healthcare_provider_factory, patient_factory, hospital_factory
    ):
        provider = healthcare_provider_factory(primary_hospital=None)
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = provider.user
        
        patient = patient_factory()
        
        # Create multiple hospitals
        hospital1 = hospital_factory()
        hospital2 = hospital_factory()
        
        # Create affiliations
        self.assign_provider_to_hospital(provider, hospital1)
        self.assign_provider_to_hospital(provider, hospital2)
        
        # Test with hospital1
        data1 = {
            'patient': patient.user.id,
            'hospital': hospital1.id,
            'diagnosis': 'Diagnosis at hospital1',
            'notes': 'Notes',
            'prescriptions': 'Prescriptions'
        }
        
        serializer1 = MedicalRecordCreateSerializer(data=data1, context={'request': request})
        assert serializer1.is_valid() is True
        
        # Test with hospital2
        data2 = {
            'patient': patient.user.id,
            'hospital': hospital2.id,
            'diagnosis': 'Diagnosis at hospital2',
            'notes': 'Notes',
            'prescriptions': 'Prescriptions'
        }
        
        serializer2 = MedicalRecordCreateSerializer(data=data2, context={'request': request})
        assert serializer2.is_valid() is True

    def test_serializer_context_required(self, patient_factory, hospital_factory):
        patient = patient_factory()
        hospital = hospital_factory()
        data = {
            'patient': patient.user.id,
            'hospital': hospital.id,
            'diagnosis': 'Test',
            'notes': 'Test',
            'prescriptions': 'Test'
        }
        
        # No context at all
        serializer = MedicalRecordCreateSerializer(data=data)
        
        with pytest.raises(Exception) as exc_info:
            serializer.is_valid(raise_exception=True)
        assert 'Authentication required' in str(exc_info.value)

class TestMedicalRecordUpdateSerializer:

    def test_update_serializer_fields(self):
        serializer = MedicalRecordUpdateSerializer()
        
        expected_fields = [
            "diagnosis",
            "notes",
            "prescriptions",
            "hospital"
        ]
        
        assert set(serializer.fields.keys()) == set(expected_fields)

    def test_update_medical_record_success(
        self, medical_record_factory, hospital_factory
    ):
        record = medical_record_factory()
        provider = record.healthcare_provider
        factory = APIRequestFactory()
        request = factory.put('/')
        request.user = provider.user
        
        new_hospital = hospital_factory()
        
        provider.hospitals.clear()  # Clear existing assignments
        ProviderHospitalAssignment.objects.create(
            healthcare_provider=provider,
            hospital=new_hospital,
            is_active=True,
            created_by=provider.user,
            updated_by=provider.user
        )
        
        data = {
            'hospital': new_hospital.id,
            'diagnosis': 'Updated diagnosis',
            'notes': 'Updated notes',
            'prescriptions': 'Updated prescriptions'
        }
        
        serializer = MedicalRecordUpdateSerializer(
            instance=record, 
            data=data, 
            context={'request': request}
        )
        
        assert serializer.is_valid() is True
        
        # Update the record
        updated_record = serializer.save()
        
        assert updated_record.hospital == new_hospital
        assert updated_record.diagnosis == 'Updated diagnosis'
        assert updated_record.notes == 'Updated notes'
        assert updated_record.prescriptions == 'Updated prescriptions'
        assert updated_record.updated_by == provider.user

    def test_partial_update(self, medical_record_factory):
        record = medical_record_factory()
        provider = record.healthcare_provider
        factory = APIRequestFactory()
        request = factory.patch('/')
        request.user = provider.user
        
        original_diagnosis = record.diagnosis
        original_hospital = record.hospital
        
        data = {
            'notes': 'Partially updated notes'
        }
        
        serializer = MedicalRecordUpdateSerializer(
            instance=record, 
            data=data, 
            context={'request': request},
            partial=True
        )
        
        assert serializer.is_valid() is True
        
        updated_record = serializer.save()
        
        assert updated_record.notes == 'Partially updated notes'
        assert updated_record.diagnosis == original_diagnosis 
        assert updated_record.hospital == original_hospital 
        assert updated_record.updated_by == provider.user
    
    def test_update_with_same_hospital(
        self, medical_record_factory
    ):
        record = medical_record_factory()
        provider = record.healthcare_provider
        factory = APIRequestFactory()
        request = factory.put('/')
        request.user = provider.user
        
        assert provider.hospitals.filter(id=record.hospital.id).exists()
        
        data = {
            'hospital': record.hospital.id,
            'diagnosis': 'Updated diagnosis',
            'notes': 'Updated notes',
            'prescriptions': 'Updated prescriptions'
        }
        
        serializer = MedicalRecordUpdateSerializer(
            instance=record, 
            data=data, 
            context={'request': request}
        )
        
        assert serializer.is_valid() is True
        
        updated_record = serializer.save()
        
        assert updated_record.hospital == record.hospital 
        assert updated_record.diagnosis == 'Updated diagnosis'
        assert updated_record.updated_by == provider.user

    def test_update_with_removed_provider(
        self, medical_record_factory
    ):
        record = medical_record_factory()
        provider = record.healthcare_provider
        factory = APIRequestFactory()
        request = factory.put('/')
        request.user = provider.user
        
        provider.is_removed = True
        provider.removed_at = timezone.now()
        provider.save()
        
        data = {
            'diagnosis': 'Updated diagnosis',
            'notes': 'Updated notes',
            'prescriptions': 'Updated prescriptions'
        }
        
        serializer = MedicalRecordUpdateSerializer(
            instance=record, 
            data=data, 
            context={'request': request}
        )
        
        assert serializer.is_valid() is True
        
        updated_record = serializer.save()
        
        assert updated_record.diagnosis == 'Updated diagnosis'
        assert updated_record.updated_by == provider.user
    
    def test_update_validation_errors(
        self, medical_record_factory
    ):
        record = medical_record_factory()
        provider = record.healthcare_provider
        factory = APIRequestFactory()
        request = factory.put('/')
        request.user = provider.user
        
        data = {
            'diagnosis': '',
            'notes': 'Updated notes',
            'prescriptions': 'Updated prescriptions'
        }
        
        serializer = MedicalRecordUpdateSerializer(
            instance=record, 
            data=data, 
            context={'request': request}
        )
        
        assert serializer.is_valid() is False
        assert 'diagnosis' in serializer.errors
    
    def test_update_authentication_required(
        self, medical_record_factory
    ):  
        record = medical_record_factory()
        
        factory = APIRequestFactory()
        request = factory.put('/')
        request.user = AnonymousUser()  # Unauthenticated user
        
        data = {
            'diagnosis': 'Updated diagnosis',
            'notes': 'Updated notes',
            'prescriptions': 'Updated prescriptions'
        }
        
        serializer = MedicalRecordUpdateSerializer(
            instance=record, 
            data=data, 
            context={'request': request}
        )
        
        with pytest.raises(DRFValidationError) as exc_info:
            serializer.is_valid(raise_exception=True)
        
        error_detail = exc_info.value.detail
        assert 'detail' in error_detail
        assert 'Authentication required' in str(error_detail['detail'][0])

    def test_update_by_different_provider(
        self, medical_record_factory, healthcare_provider_factory
    ):
        record = medical_record_factory()
        different_provider = healthcare_provider_factory()
        
        different_provider.hospitals.clear()
        ProviderHospitalAssignment.objects.create(
            healthcare_provider=different_provider,
            hospital=record.hospital,
            is_active=True,
            created_by=different_provider.user,
            updated_by=different_provider.user
        )
        
        factory = APIRequestFactory()
        request = factory.put('/')
        request.user = different_provider.user  # Different provider
        
        data = {
            'hospital': record.hospital.id,
            'diagnosis': 'Updated by different provider',
            'notes': 'Updated notes',
            'prescriptions': 'Updated prescriptions'
        }
        
        serializer = MedicalRecordUpdateSerializer(
            instance=record, 
            data=data, 
            context={'request': request}
        )
        
        assert serializer.is_valid() is True
        
        updated_record = serializer.save()
        assert updated_record.diagnosis == 'Updated by different provider'
        assert updated_record.updated_by == different_provider.user

    def test_update_with_inactive_hospital_assignment(
        self, medical_record_factory, hospital_factory
    ):
        record = medical_record_factory()
        provider = record.healthcare_provider
        factory = APIRequestFactory()
        request = factory.put('/')
        request.user = provider.user
        
        new_hospital = hospital_factory()
        
        provider.hospitals.clear()  # Clear existing assignments
        ProviderHospitalAssignment.objects.create(
            healthcare_provider=provider,
            hospital=new_hospital,
            is_active=False,  # Inactive!
            end_datetime_utc=timezone.now(),
            created_by=provider.user,
            updated_by=provider.user
        )
        
        data = {
            'hospital': new_hospital.id,
            'diagnosis': 'Updated diagnosis',
            'notes': 'Updated notes',
            'prescriptions': 'Updated prescriptions'
        }
        
        serializer = MedicalRecordUpdateSerializer(
            instance=record, 
            data=data, 
            context={'request': request}
        )
        
        assert serializer.is_valid() is False
        assert 'hospital' in serializer.errors
        assert 'Provider is not affiliated with this hospital' in str(serializer.errors['hospital'][0])
    
    def test_update_with_removed_hospital(
        self, medical_record_factory, hospital_factory
    ):
        record = medical_record_factory()
        provider = record.healthcare_provider
        factory = APIRequestFactory()
        request = factory.put('/')
        request.user = provider.user
        
        removed_hospital = hospital_factory(is_removed=True, removed_at=timezone.now())
        
        provider.hospitals.clear()
        ProviderHospitalAssignment.objects.create(
            healthcare_provider=provider,
            hospital=removed_hospital,
            is_active=True,
            created_by=provider.user,
            updated_by=provider.user
        )
        
        data = {
            'hospital': removed_hospital.id,
            'diagnosis': 'Updated diagnosis',
            'notes': 'Updated notes',
            'prescriptions': 'Updated prescriptions'
        }
        
        serializer = MedicalRecordUpdateSerializer(
            instance=record, 
            data=data, 
            context={'request': request}
        )
        
        with pytest.raises(DRFValidationError) as exc_info:
            serializer.is_valid(raise_exception=True)
        assert 'Selected hospital is no longer active' in str(exc_info.value.detail['hospital'][0])

    def test_update_empty_notes_validation(
        self, medical_record_factory
    ):
        record = medical_record_factory()
        provider = record.healthcare_provider
        factory = APIRequestFactory()
        request = factory.put('/')
        request.user = provider.user
        
        data = {
            'hospital': record.hospital.id,
            'diagnosis': 'Updated diagnosis',
            'notes': '   ',
            'prescriptions': 'Updated prescriptions'
        }
        
        serializer = MedicalRecordUpdateSerializer(
            instance=record, 
            data=data, 
            context={'request': request}
        )
        
        assert serializer.is_valid() is False
        assert 'notes' in serializer.errors
        assert 'This field may not be blank' in str(serializer.errors['notes'][0])
    
    def test_update_empty_prescriptions_validation(
        self, medical_record_factory
    ):
        record = medical_record_factory()
        provider = record.healthcare_provider
        factory = APIRequestFactory()
        request = factory.put('/')
        request.user = provider.user
        
        data = {
            'hospital': record.hospital.id,
            'diagnosis': 'Updated diagnosis',
            'notes': 'Updated notes',
            'prescriptions': ''
        }
        
        serializer = MedicalRecordUpdateSerializer(
            instance=record, 
            data=data, 
            context={'request': request}
        )
        
        assert serializer.is_valid() is False
        assert 'prescriptions' in serializer.errors
        assert 'This field may not be blank' in str(serializer.errors['prescriptions'][0])

    def test_update_no_fields_changed(
        self, medical_record_factory
    ):
        record = medical_record_factory()
        provider = record.healthcare_provider
        factory = APIRequestFactory()
        request = factory.put('/')
        request.user = provider.user
        
        # Send same data
        data = {
            'hospital': record.hospital.id,
            'diagnosis': record.diagnosis,
            'notes': record.notes,
            'prescriptions': record.prescriptions
        }
        
        serializer = MedicalRecordUpdateSerializer(
            instance=record, 
            data=data, 
            context={'request': request}
        )
        
        assert serializer.is_valid() is True
        
        updated_record = serializer.save()
        # All fields should remain the same
        assert updated_record.hospital == record.hospital
        assert updated_record.diagnosis == record.diagnosis
        assert updated_record.notes == record.notes
        assert updated_record.prescriptions == record.prescriptions
        assert updated_record.updated_by == provider.user

class TestMedicalRecordListSerializer:
    
    def test_list_serializer_fields(self):
        serializer = MedicalRecordListSerializer()
        
        expected_fields = [
            'id',
            'patient_id',
            'patient_name',
            'provider_id',
            'provider_name',
            'hospital_name',
            'diagnosis',
            'created_at',
            'updated_at'
        ]
        
        actual_fields = set(serializer.fields.keys())
        expected_fields_set = set(expected_fields)
        
        assert actual_fields == expected_fields_set, \
            f"Expected fields: {expected_fields_set}, Got: {actual_fields}"
        
    def test_all_fields_are_read_only(self):
        serializer = MedicalRecordListSerializer()
        
        for field_name, field in serializer.fields.items():
            assert field.read_only is True, \
                f"Field '{field_name}' should be read-only but isn't"
            
    def test_provider_name_field(self, medical_record_factory):
        record = medical_record_factory()
        serializer = MedicalRecordListSerializer(record)
        
        expected_name = record.healthcare_provider.user.get_full_name()
        assert serializer.data['providerName'] == expected_name
        
        # Test with different names
        record.healthcare_provider.user.first_name = "Dr. Jane"
        record.healthcare_provider.user.last_name = "Smith"
        record.healthcare_provider.user.save()
        
        serializer = MedicalRecordListSerializer(record)
        assert serializer.data['providerName'] == "Dr. Jane Smith"
    
    def test_hospital_name_field(self, medical_record_factory):
        record = medical_record_factory()
        serializer = MedicalRecordListSerializer(record)
        
        assert serializer.data['hospitalName'] == record.hospital.name
        
        # Test with different hospital name
        record.hospital.name = "General Hospital"
        record.hospital.save()
        
        serializer = MedicalRecordListSerializer(record)
        assert serializer.data['hospitalName'] == "General Hospital"

    def test_serializer_with_multiple_records(self, medical_record_factory):
        records = [medical_record_factory() for _ in range(3)]
        
        serializer = MedicalRecordListSerializer(records, many=True)
        
        assert len(serializer.data) == 3
        
        for i, data in enumerate(serializer.data):
            record = records[i]
            assert data['id'] == record.id
            assert data['patientId'] == str(record.patient.user.id)
            assert data['patientName'] == record.patient.user.get_full_name()
            assert data['providerId'] == str(record.healthcare_provider.user.id)
            assert data['providerName'] == record.healthcare_provider.user.get_full_name()
            assert data['hospitalName'] == record.hospital.name
            assert data['diagnosis'] == record.diagnosis
    
    def test_serializer_with_removed_hospital(self, medical_record_factory):
        record = medical_record_factory()
        
        record.hospital.is_removed = True
        record.hospital.removed_at = timezone.now()
        record.hospital.save()
        
        serializer = MedicalRecordListSerializer(record)
        
        assert serializer.data['hospitalName'] == record.hospital.name

    def test_serializer_with_removed_provider(self, medical_record_factory):
        record = medical_record_factory()
        
        record.healthcare_provider.is_removed = True
        record.healthcare_provider.removed_at = timezone.now()
        record.healthcare_provider.save()
        
        serializer = MedicalRecordListSerializer(record)
        
        assert serializer.data['providerId'] == str(record.healthcare_provider.user.id)
        assert serializer.data['providerName'] == record.healthcare_provider.user.get_full_name()
    
    def test_serializer_with_removed_patient(self, medical_record_factory):
        record = medical_record_factory()
        
        serializer = MedicalRecordListSerializer(record)
        
        assert serializer.data['patientId'] == str(record.patient.user.id)
        assert serializer.data['patientName'] == record.patient.user.get_full_name()

class TestMedicalRecordDetailSerializer:
    def test_detail_serializer_fields(self):
        serializer = MedicalRecordDetailSerializer()
        
        expected_fields = [
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
        
        actual_fields = set(serializer.fields.keys())
        expected_fields_set = set(expected_fields)
        
        assert actual_fields == expected_fields_set, \
            f"Expected fields: {expected_fields_set}, Got: {actual_fields}"
        
    def test_all_fields_are_read_only(self):
        serializer = MedicalRecordDetailSerializer()
        
        for field_name, field in serializer.fields.items():
            assert field.read_only is True, \
                f"Field '{field_name}' should be read-only but isn't"
    
    def test_patient_details_values(self, medical_record_factory):
        record = medical_record_factory()
        
        # Set some test values on patient
        record.patient.blood_type = "O+"
        record.patient.allergies = "Penicillin, Peanuts"
        record.patient.chronic_conditions = "Hypertension"
        record.patient.current_medications = "Lisinopril 10mg daily"
        record.patient.insurance = "Blue Cross"
        record.patient.weight = 70  # kg
        record.patient.height = 175  # cm
        record.patient.save()
        
        # Set user details
        record.patient.user.date_of_birth = timezone.datetime(1980, 1, 1).date()
        record.patient.user.image = "profile.jpg"
        record.patient.user.save()
        
        serializer = MedicalRecordDetailSerializer(record)
        patient_details = serializer.data['patientDetails']
        
        assert patient_details['id'] == record.patient.user.id
        assert patient_details['bloodType'] == "O+"
        assert patient_details['allergies'] == "Penicillin, Peanuts"
        assert patient_details['chronicConditions'] == "Hypertension"
        assert patient_details['currentMedications'] == "Lisinopril 10mg daily"
        assert patient_details['insurance'] == "Blue Cross"
        assert patient_details['weight'] == 70
        assert patient_details['height'] == 175
        assert patient_details['fullName'] == record.patient.user.get_full_name()
        assert patient_details['dateOfBirth'].strftime("%Y-%m-%d") == "1980-01-01"
        assert patient_details['image'] == "profile.jpg"
        
    def test_provider_details_values(self, medical_record_factory, speciality_factory):
        record = medical_record_factory()
        
        speciality = speciality_factory(name="Cardiology")
        record.healthcare_provider.speciality = speciality
        record.healthcare_provider.license_number = "MD123456"
        record.healthcare_provider.save()
        
        record.healthcare_provider.user.first_name = "Dr. John"
        record.healthcare_provider.user.last_name = "Smith"
        record.healthcare_provider.user.save()
        
        serializer = MedicalRecordDetailSerializer(record)
        provider_details = serializer.data['providerDetails']
        
        assert provider_details['id'] == record.healthcare_provider.user.id
        assert provider_details['specialityName'] == "Cardiology"
        assert provider_details['licenseNumber'] == "MD123456"
        assert provider_details['fullName'] == "Dr. John Smith"

    def test_hospital_details_values(self, medical_record_factory):
        record = medical_record_factory()
        
        # Update hospital details
        record.hospital.name = "General Hospital"
        record.hospital.phone_number = "555-1234"
        record.hospital.timezone = "America/New_York"
        record.hospital.save()
        
        serializer = MedicalRecordDetailSerializer(record)
        hospital_details = serializer.data['hospitalDetails']
        
        assert hospital_details['id'] == record.hospital.id
        assert hospital_details['name'] == "General Hospital"
        assert hospital_details['phoneNumber'] == "555-1234"
        assert hospital_details['timezone'] == "America/New_York"

    def test_created_by_and_updated_by_names(self, medical_record_factory, provider_factory):
        provider1 = provider_factory()
        provider2 = provider_factory()

        record = medical_record_factory()
        
        record.created_by = provider1.user
        record.updated_by = provider2.user
        record.save()
        
        serializer = MedicalRecordDetailSerializer(record)
        
        assert serializer.data['createdByName'] == provider1.user.get_full_name()
        assert serializer.data['updatedByName'] == provider2.user.get_full_name()
        assert serializer.data['createdBy'] == provider1.user.id
        assert serializer.data['updatedBy'] == provider2.user.id

    def test_soft_delete_fields(self, medical_record_factory):
        record = medical_record_factory()
        
        # Mark as removed
        record.is_removed = True
        record.removed_at = timezone.now()
        record.save()
        
        serializer = MedicalRecordDetailSerializer(record)
        
        assert serializer.data['isRemoved'] is True
        assert serializer.data['removedAt'] is not None
        
        iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$'
        assert re.match(iso_pattern, serializer.data['removedAt']) is not None

    def test_medical_record_content_fields(self, medical_record_factory):
        record = medical_record_factory()
        
        record.diagnosis = "Acute bronchitis"
        record.notes = "Patient presented with cough and fever for 3 days."
        record.prescriptions = "Amoxicillin 500mg TID for 7 days\nAcetaminophen PRN for fever"
        record.save()
        
        serializer = MedicalRecordDetailSerializer(record)
        
        assert serializer.data['diagnosis'] == "Acute bronchitis"
        assert serializer.data['notes'] == "Patient presented with cough and fever for 3 days."
        assert serializer.data['prescriptions'] == "Amoxicillin 500mg TID for 7 days\nAcetaminophen PRN for fever"

    def test_serializer_with_removed_hospital(self, medical_record_factory):
        record = medical_record_factory()
        
        # Mark hospital as removed
        record.hospital.is_removed = True
        record.hospital.removed_at = timezone.now()
        record.hospital.save()
        
        serializer = MedicalRecordDetailSerializer(record)
        
        # Should still serialize hospital details
        hospital_details = serializer.data['hospitalDetails']
        assert hospital_details['name'] == record.hospital.name
        assert hospital_details['id'] == record.hospital.id

    def test_serializer_with_removed_provider(self, medical_record_factory):
        record = medical_record_factory()
        
        # Mark provider as removed
        record.healthcare_provider.is_removed = True
        record.healthcare_provider.removed_at = timezone.now()
        record.healthcare_provider.save()
        
        serializer = MedicalRecordDetailSerializer(record)
        
        # Should still serialize provider details
        provider_details = serializer.data['providerDetails']
        assert provider_details['fullName'] == record.healthcare_provider.user.get_full_name()
        assert provider_details['licenseNumber'] == record.healthcare_provider.license_number

    def test_serializer_with_multiple_records(self, medical_record_factory):
        records = [medical_record_factory() for _ in range(3)]
        
        serializer = MedicalRecordDetailSerializer(records, many=True)
        
        assert len(serializer.data) == 3
        
        for i, data in enumerate(serializer.data):
            record = records[i]
            
            # Check basic fields
            assert data['id'] == record.id
            assert data['diagnosis'] == record.diagnosis
            assert data['notes'] == record.notes
            assert data['prescriptions'] == record.prescriptions
            
            # Check nested details exist
            assert 'patientDetails' in data
            assert 'providerDetails' in data
            assert 'hospitalDetails' in data
            
            # Check patient details
            assert data['patientDetails']['id'] == record.patient.user.id
            assert data['patientDetails']['fullName'] == record.patient.user.get_full_name()