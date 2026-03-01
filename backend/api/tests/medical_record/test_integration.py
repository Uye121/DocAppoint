import pytest
from django.urls import reverse
from rest_framework import status
from django.utils import timezone
from datetime import timedelta

from api.models import MedicalRecord, Appointment


pytestmark = pytest.mark.django_db


class TestMedicalRecordFlow:

    def test_provider_creates_medical_record_flow(self, authenticated_provider_client,
                                                  patient_factory, appointment_factory,
                                                  hospital_factory):
        """Test complete flow: provider creates medical record for completed appointment"""
        provider_client, provider = authenticated_provider_client()
        patient = patient_factory()
        hospital = provider.primary_hospital or hospital_factory()
        
        appointment = appointment_factory(
            healthcare_provider=provider,
            patient=patient,
            location=hospital,
            appointment_start_datetime_utc=timezone.now() - timedelta(days=1),
            appointment_end_datetime_utc=timezone.now() - timedelta(days=1, minutes=-30),
            status=Appointment.Status.COMPLETED
        )
        
        # Provider creates medical record for the appointment
        medical_record_url = reverse("medical_record-list")
        record_data = {
            "patient_id": patient.user_id,
            "hospital_id": hospital.id,
            "appointment_id": appointment.id,
            "diagnosis": "Acute bronchitis",
            "notes": "Patient presented with cough and fever. Prescribed antibiotics.",
            "prescriptions": "Amoxicillin 500mg twice daily for 7 days"
        }
        
        response = provider_client.post(medical_record_url, record_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        
        record_id = response.data["id"]
        
        medical_record = MedicalRecord.objects.get(id=record_id)
        assert medical_record.healthcare_provider == provider
        assert medical_record.patient == patient
        assert medical_record.appointment == appointment
        assert medical_record.diagnosis == "Acute bronchitis"
        
        # Fail to create another record for the same appointment
        response = provider_client.post(medical_record_url, record_data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already linked to another medical record" in str(response.data)

    def test_patient_views_their_medical_records(self, authenticated_patient_client,
                                                 provider_factory, medical_record_factory):
        """Test patient can view their own medical records"""
        patient_client, patient = authenticated_patient_client()
        provider = provider_factory()
        
        record1 = medical_record_factory(
            patient=patient,
            healthcare_provider=provider,
            diagnosis="Hypertension",
            notes="Follow-up in 3 months"
        )
        record2 = medical_record_factory(
            patient=patient,
            healthcare_provider=provider,
            diagnosis="Diabetes Type 2",
            notes="HbA1c improved"
        )
        
        # Create record for different patient
        other_patient_record = medical_record_factory()
        
        list_url = reverse("medical_record-list")
        response = patient_client.get(list_url)
        assert response.status_code == status.HTTP_200_OK
        
        record_ids = [r["id"] for r in response.data]
        assert record1.id in record_ids
        assert record2.id in record_ids
        assert other_patient_record.id not in record_ids
        
        detail_url = reverse("medical_record-detail", args=[record1.id])
        response = patient_client.get(detail_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["diagnosis"] == "Hypertension"
        assert "patientDetails" in response.data
        assert response.data["patientDetails"]["fullName"] == patient.user.get_full_name()

    def test_provider_updates_medical_record(self, authenticated_provider_client,
                                             medical_record_factory):
        """Test provider can update their own medical records"""
        provider_client, provider = authenticated_provider_client()
        
        medical_record = medical_record_factory(healthcare_provider=provider)
        
        # Update the record
        detail_url = reverse("medical_record-detail", args=[medical_record.id])
        update_data = {
            "diagnosis": "Updated diagnosis - Severe hypertension",
            "notes": "Patient showing improvement with medication",
            "prescriptions": "Lisinopril 10mg daily"
        }
        
        response = provider_client.patch(detail_url, update_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        
        medical_record.refresh_from_db()
        assert medical_record.diagnosis == "Updated diagnosis - Severe hypertension"
        assert "Lisinopril" in medical_record.prescriptions
        assert medical_record.updated_by == provider.user

    def test_provider_can_update_others_records(self, authenticated_provider_client,
                                                provider_factory, medical_record_factory):
        """Test provider can update another provider's records"""
        provider_client, provider1 = authenticated_provider_client()
        
        # Create another provider and their record
        provider2 = provider_factory()
        other_record = medical_record_factory(healthcare_provider=provider2)
        
        # Update another provider's records
        detail_url = reverse("medical_record-detail", args=[other_record.id])
        update_data = {
            "diagnosis": "Updated by different provider",
            "notes": "Collaborative care note added"
        }
        
        response = provider_client.patch(detail_url, update_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        
        other_record.refresh_from_db()
        assert other_record.diagnosis == "Updated by different provider"
        assert other_record.notes == "Collaborative care note added"
        
        assert other_record.updated_by == provider1.user
        
        # Original provider can still access and update
        from rest_framework.test import APIClient
        provider2_client = APIClient()
        provider2_client.force_authenticate(user=provider2.user)
        
        response = provider2_client.get(detail_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["diagnosis"] == "Updated by different provider"

    def test_provider_soft_deletes_medical_record(self, authenticated_provider_client,
                                                  medical_record_factory):
        """Test provider can soft delete their medical records"""
        provider_client, provider = authenticated_provider_client()
        
        medical_record = medical_record_factory(healthcare_provider=provider)
        
        # Soft delete the record
        detail_url = reverse("medical_record-detail", args=[medical_record.id])
        response = provider_client.delete(detail_url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        medical_record.refresh_from_db()
        assert medical_record.is_removed is True
        assert medical_record.removed_at is not None
        
        # Record no longer appears in list
        list_url = reverse("medical_record-list")
        response = provider_client.get(list_url)
        assert medical_record.id not in [r["id"] for r in response.data]

    def test_admin_can_view_soft_deleted_records(self, authenticated_admin_client, medical_record_factory):
        """Test admin/staff can view and restore soft-deleted records"""
        medical_record = medical_record_factory(is_removed=True)
        admin_client, _ = authenticated_admin_client()
        
        # Admin remove records
        removed_url = reverse("medical_record-removed")
        response = admin_client.get(removed_url)
        assert response.status_code == status.HTTP_200_OK
        assert medical_record.id in [r["id"] for r in response.data]
        
        # Admin restores the record
        restore_url = reverse("medical_record-restore", args=[medical_record.id])
        response = admin_client.post(restore_url)
        assert response.status_code == status.HTTP_200_OK
        assert "restored successfully" in response.data["detail"]
        
        medical_record.refresh_from_db()
        assert medical_record.is_removed is False
        assert medical_record.removed_at is None

    def test_medical_record_stats_endpoint(self, authenticated_provider_client,
                                           medical_record_factory, authenticated_patient_client):
        """Test the stats endpoint for providers and patients"""
        # Test provider stats
        provider_client, provider = authenticated_provider_client()
        
        for _ in range(5):
            medical_record_factory(healthcare_provider=provider)
        
        # Create old record (beyond 30 days)
        medical_record_factory(
            healthcare_provider=provider,
            created_at=timezone.now() - timedelta(days=45)
        )
        
        stats_url = reverse("medical_record-stats")
        response = provider_client.get(stats_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["role"] == "provider"
        assert response.data["total_records"] >= 6
        assert "recent_records" in response.data
        
        patient_client, patient = authenticated_patient_client()
        
        # Create records for this patient
        for _ in range(3):
            medical_record_factory(patient=patient)
        
        response = patient_client.get(stats_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["role"] == "patient"
        assert response.data["total_records"] >= 3

    def test_medical_record_filtering_and_search(self, authenticated_provider_client,
                                                 patient_factory, hospital_factory,
                                                 medical_record_factory):
        """Test filtering and searching medical records"""
        provider_client, provider = authenticated_provider_client()
        
        patient1 = patient_factory(user__first_name="Alice", user__last_name="Johnson")
        patient2 = patient_factory(user__first_name="Bob", user__last_name="Smith")
        hospital1 = hospital_factory(name="City General")
        hospital2 = hospital_factory(name="Community Health")
        
        record1 = medical_record_factory(
            healthcare_provider=provider,
            patient=patient1,
            hospital=hospital1,
            diagnosis="Diabetes mellitus type 2",
            notes="Patient needs dietary consult"
        )
        record2 = medical_record_factory(
            healthcare_provider=provider,
            patient=patient2,
            hospital=hospital1,
            diagnosis="Hypertension",
            notes="Blood pressure elevated"
        )
        record3 = medical_record_factory(
            healthcare_provider=provider,
            patient=patient1,
            hospital=hospital2,
            diagnosis="Asthma",
            notes="Inhaler prescription renewed"
        )
        
        list_url = reverse("medical_record-list")
        
        # Filter by patient
        response = provider_client.get(list_url, {"patient": patient1.user_id})
        assert len(response.data) == 2
        record_ids = [r["id"] for r in response.data]
        assert record1.id in record_ids
        assert record3.id in record_ids
        assert record2.id not in record_ids
        
        # Filter by hospital
        response = provider_client.get(list_url, {"hospital": hospital1.id})
        assert len(response.data) == 2
        assert record1.id in [r["id"] for r in response.data]
        assert record2.id in [r["id"] for r in response.data]
        
        # Search by diagnosis
        response = provider_client.get(list_url, {"search": "diabetes"})
        assert len(response.data) == 1
        assert response.data[0]["id"] == record1.id
        
        # Search by patient name
        response = provider_client.get(list_url, {"search": "Alice"})
        assert len(response.data) == 2
        assert record1.id in [r["id"] for r in response.data]
        assert record3.id in [r["id"] for r in response.data]