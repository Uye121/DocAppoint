import pytest
from django.utils import timezone

from api.models import MedicalRecord

pytestmark = pytest.mark.django_db

class TestMedicalRecordModel:
    @pytest.fixture
    def record_data(self, patient_factory, healthcare_provider_factory, hospital_factory):
        patient = patient_factory()
        provider = healthcare_provider_factory()
        hospital = hospital_factory()
        
        return {
            "patient": patient,
            "healthcare_provider": provider,
            "hospital": hospital,
            "diagnosis": "Common cold",
            "notes": "Patient presented with symptoms",
            "prescriptions": "Rest and fluids",
            "created_by": provider.user,
            "updated_by": provider.user,
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
        assert str(record) == f"Medical Record: {record.patient} - {record.updated_at}"

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

    def test_medical_record_required_fields(self, record_data):
        # Test without diagnosis
        record_data.pop("diagnosis")
        with pytest.raises(Exception):
            MedicalRecord.objects.create(**record_data)
        
        # Test without patient
        record_data["diagnosis"] = "Test"
        patient = record_data.pop("patient")
        with pytest.raises(Exception):
            MedicalRecord.objects.create(**record_data)

        record_data["patient"] = patient
        record_data["hospital"] = None
        with pytest.raises(Exception):
            MedicalRecord.objects.create(**record_data)

    def test_medical_record_ordering(self, record_data):
        record1 = MedicalRecord.objects.create(**record_data)
        record2 = MedicalRecord.objects.create(**record_data)
        
        record1.created_at = timezone.now() - timezone.timedelta(days=1)
        record1.save()
        
        records = MedicalRecord.objects.all()
        assert records[0] == record2 
        assert records[1] == record1