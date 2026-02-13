import pytest
from django.utils import timezone

from api.models import MedicalRecord

pytestmark = pytest.mark.django_db

class TestMedicalRecordModel:
    @pytest.fixture
    def record_data(self, patient_factory, healthcare_provider_factory, hospital_factory, appointment_factory):
        patient = patient_factory()
        provider = healthcare_provider_factory()
        hospital = hospital_factory()
        appointment = appointment_factory()
        
        return {
            "patient": patient,
            "healthcare_provider": provider,
            "hospital": hospital,
            "diagnosis": "Common cold",
            "notes": "Patient presented with symptoms",
            "prescriptions": "Rest and fluids",
            "created_by": provider.user,
            "updated_by": provider.user,
            "appointment": appointment,
        }
    
    def test_create_medical_record(self, record_data):
        record = MedicalRecord.objects.create(**record_data)
        
        assert record.id is not None
        assert record.patient == record_data["patient"]
        assert record.healthcare_provider == record_data["healthcare_provider"]
        assert record.hospital == record_data["hospital"]
        assert record.diagnosis == "Common cold"
        assert record.is_removed is False
        assert record.removed_at is None
        assert record.appointment is not None
        assert str(record) == f"Medical Record: {record.patient} - {record.updated_at}"

    def test_create_medical_record_with_appointment(self, record_data, appointment_factory):
        appointment = appointment_factory()
        
        record_data["appointment"] = appointment
        
        record = MedicalRecord.objects.create(**record_data)
        
        assert record.id is not None
        assert record.appointment == appointment
        # Verify the reverse relationship works
        assert appointment.medical_record == record

    def test_appointment_one_to_one_constraint(self, record_data, appointment_factory):
        appointment = appointment_factory()
        
        # Create first medical record with the appointment
        record_data["appointment"] = appointment
        MedicalRecord.objects.create(**record_data)
        
        # Try to create second medical record with same appointment
        with pytest.raises(Exception):
            MedicalRecord.objects.create(**record_data)

    def test_medical_record_soft_delete(self, record_data):
        record = MedicalRecord.objects.create(**record_data)
        
        # Soft delete the record
        record.is_removed = True
        record.removed_at = timezone.now()
        record.save()
        
        record.refresh_from_db()
        assert record.is_removed is True
        assert record.removed_at is not None
        
        # Should still exist in database
        assert MedicalRecord.objects.filter(id=record.id).exists()

    def test_medical_record_required_fields(self, record_data, hospital_factory):
        # Test without diagnosis
        record_data.pop("diagnosis")
        with pytest.raises(Exception):
            MedicalRecord.objects.create(**record_data)
        
        # Test without patient
        record_data["diagnosis"] = "Test"
        patient = record_data.pop("patient")
        with pytest.raises(Exception):
            MedicalRecord.objects.create(**record_data)

        # Test without hospital
        record_data["patient"] = patient
        record_data["hospital"] = None
        with pytest.raises(Exception):
            MedicalRecord.objects.create(**record_data)
        
        # NEW: Test without healthcare_provider (should also fail)
        record_data["hospital"] = hospital_factory()
        record_data.pop("healthcare_provider")
        with pytest.raises(Exception):
            MedicalRecord.objects.create(**record_data)
