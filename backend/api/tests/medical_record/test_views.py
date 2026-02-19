import pytest
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate
from django.utils import timezone
from django.urls import reverse

from api.models import MedicalRecord, ProviderHospitalAssignment
from api.views import MedicalRecordViewSet

pytestmark = pytest.mark.django_db


class TestMedicalRecordViewSet:
    def get_viewset(self, request=None, **kwargs):
        viewset = MedicalRecordViewSet()
        if request:
            viewset.request = request
            viewset.format_kwarg = None
            viewset.kwargs = kwargs
        return viewset

    def get_url(self, viewname, **kwargs):
        return reverse(f"medical_record:{viewname}", kwargs=kwargs)

    def test_get_queryset_for_patient(self, patient_factory, medical_record_factory):
        patient1 = patient_factory()
        patient2 = patient_factory()

        record1 = medical_record_factory(patient=patient1)
        record2 = medical_record_factory(patient=patient2)
        record3 = medical_record_factory(patient=patient1)

        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = patient1.user

        viewset = self.get_viewset(request)
        viewset.action = "list"

        queryset = viewset.get_queryset()

        assert queryset.count() == 2
        assert record1 in queryset
        assert record3 in queryset
        assert record2 not in queryset

    def test_get_queryset_for_provider(
        self, healthcare_provider_factory, medical_record_factory
    ):
        provider1 = healthcare_provider_factory()
        provider2 = healthcare_provider_factory()

        record1 = medical_record_factory(healthcare_provider=provider1)
        record2 = medical_record_factory(healthcare_provider=provider2)
        record3 = medical_record_factory(healthcare_provider=provider1)

        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = provider1.user

        viewset = self.get_viewset(request)
        viewset.action = "list"

        queryset = viewset.get_queryset()

        # Provider1 should only see records they created
        assert queryset.count() == 2
        assert record1 in queryset
        assert record3 in queryset
        assert record2 not in queryset

    def test_get_queryset_for_other_user(self, user_factory, medical_record_factory):
        user = user_factory()

        # Create some records
        medical_record_factory()
        medical_record_factory()

        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = user

        viewset = self.get_viewset(request)
        viewset.action = "list"

        queryset = viewset.get_queryset()

        # Regular user should see nothing
        assert queryset.count() == 0

    def test_get_queryset_excludes_removed_records(self, medical_record_factory):
        active_record = medical_record_factory(is_removed=False)
        removed_record = medical_record_factory(
            is_removed=True, removed_at=timezone.now()
        )

        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = active_record.healthcare_provider.user

        viewset = self.get_viewset(request)
        viewset.action = "list"

        queryset = viewset.get_queryset()

        # Should only see active records
        assert queryset.count() == 1
        assert active_record in queryset
        assert removed_record not in queryset

    def test_list_records_as_provider(
        self, healthcare_provider_factory, medical_record_factory
    ):
        provider = healthcare_provider_factory()

        [medical_record_factory(healthcare_provider=provider) for _ in range(3)]

        factory = APIRequestFactory()
        request = factory.get(reverse("medical_record-list"))

        force_authenticate(request, user=provider.user)
        view = MedicalRecordViewSet.as_view({"get": "list"})
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3

    def test_list_records_as_patient(self, patient_factory, medical_record_factory):
        patient = patient_factory()

        [medical_record_factory(patient=patient) for _ in range(2)]
        medical_record_factory()

        factory = APIRequestFactory()
        request = factory.get(reverse("medical_record-list"))

        force_authenticate(request, user=patient.user)
        view = MedicalRecordViewSet.as_view({"get": "list"})
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_create_medical_record_as_provider(
        self, provider_factory, patient_factory, hospital_factory, appointment_factory
    ):
        provider = provider_factory()
        patient = patient_factory()
        hospital = hospital_factory()
        appointment = appointment_factory(patient=patient, healthcare_provider=provider)

        ProviderHospitalAssignment.objects.create(
            healthcare_provider=provider,
            hospital=hospital,
            is_active=True,
            created_by=provider.user,
            updated_by=provider.user,
        )

        data = {
            "patient_id": patient.user.id,
            "hospital_id": hospital.id,
            "appointment_id": appointment.id,
            "diagnosis": "Test diagnosis",
            "notes": "Test notes",
            "prescriptions": "Test prescriptions",
        }

        factory = APIRequestFactory()
        request = factory.post(reverse("medical_record-list"), data=data, format="json")
        force_authenticate(request, user=provider.user)

        view = MedicalRecordViewSet.as_view({"post": "create"})
        response = view(request)

        assert response.status_code == status.HTTP_201_CREATED
        assert MedicalRecord.objects.count() == 1

        record = MedicalRecord.objects.first()
        assert record.patient == patient
        assert record.healthcare_provider == provider
        assert record.hospital == hospital
        assert record.diagnosis == "Test diagnosis"

    def test_create_medical_record_as_non_provider(
        self, patient_factory, hospital_factory
    ):
        patient = patient_factory()
        hospital = hospital_factory()

        data = {
            "patient_id": patient.user.id,
            "hospital_id": hospital.id,
            "diagnosis": "Test diagnosis",
            "notes": "Test notes",
            "prescriptions": "Test prescriptions",
        }

        factory = APIRequestFactory()
        request = factory.post(reverse("medical_record-list"), data=data, format="json")
        force_authenticate(request, user=patient.user)

        view = MedicalRecordViewSet.as_view({"post": "create"})
        response = view(request)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_retrieve_record_as_owner_provider(self, medical_record_factory):
        record = medical_record_factory()
        provider = record.healthcare_provider

        factory = APIRequestFactory()
        request = factory.get(
            reverse("medical_record-detail", kwargs={"pk": record.id})
        )
        force_authenticate(request, user=provider.user)

        view = MedicalRecordViewSet.as_view({"get": "retrieve"})
        response = view(request, pk=record.id)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == record.id
        assert response.data["diagnosis"] == record.diagnosis

    def test_retrieve_record_unauthorized(self, medical_record_factory, user_factory):
        record = medical_record_factory()
        unauthorized_user = user_factory()

        factory = APIRequestFactory()
        request = factory.get(
            reverse("medical_record-detail", kwargs={"pk": record.id})
        )
        force_authenticate(request, user=unauthorized_user)

        view = MedicalRecordViewSet.as_view({"get": "retrieve"})
        response = view(request, pk=record.id)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_stats_action_as_provider(
        self, healthcare_provider_factory, medical_record_factory
    ):
        provider = healthcare_provider_factory()

        # Create records for this provider
        [medical_record_factory(healthcare_provider=provider) for _ in range(5)]

        factory = APIRequestFactory()
        request = factory.get(reverse("medical_record-stats"))
        force_authenticate(request, user=provider.user)

        view = MedicalRecordViewSet.as_view({"get": "stats"})
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_records"] == 5
        assert response.data["role"] == "provider"

    def test_stats_action_as_patient(self, patient_factory, medical_record_factory):
        patient = patient_factory()

        [medical_record_factory(patient=patient) for _ in range(3)]

        factory = APIRequestFactory()
        request = factory.get(reverse("medical_record-stats"))
        force_authenticate(request, user=patient.user)

        view = MedicalRecordViewSet.as_view({"get": "stats"})
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_records"] == 3
        assert response.data["role"] == "patient"

    def test_filter_by_patient(self, patient_factory, medical_record_factory):
        patient1 = patient_factory()
        patient2 = patient_factory()

        record1 = medical_record_factory(patient=patient1)
        provider = record1.healthcare_provider

        medical_record_factory(healthcare_provider=provider, patient=patient2)
        medical_record_factory(healthcare_provider=provider, patient=patient1)

        factory = APIRequestFactory()
        url = reverse("medical_record-list")
        request = factory.get(f"{url}?patient={patient1.user.id}")
        force_authenticate(request, user=provider.user)

        view = MedicalRecordViewSet.as_view({"get": "list"})
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_filter_by_hospital(self, medical_record_factory, hospital_factory):
        hospital1 = hospital_factory()
        hospital2 = hospital_factory()

        # Create records in both hospitals
        record1 = medical_record_factory(hospital=hospital1)
        provider = record1.healthcare_provider

        medical_record_factory(healthcare_provider=provider, hospital=hospital2)
        medical_record_factory(healthcare_provider=provider, hospital=hospital1)

        factory = APIRequestFactory()
        url = reverse("medical_record-list")
        request = factory.get(f"{url}?hospital={hospital1.id}")
        force_authenticate(request, user=provider.user)

        view = MedicalRecordViewSet.as_view({"get": "list"})
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_search_by_diagnosis(self, medical_record_factory):
        record1 = medical_record_factory(diagnosis="COVID-19 infection")
        provider = record1.healthcare_provider

        medical_record_factory(healthcare_provider=provider, diagnosis="Common cold")
        medical_record_factory(
            healthcare_provider=provider, diagnosis="COVID-19 pneumonia"
        )

        factory = APIRequestFactory()
        url = reverse("medical_record-list")
        request = factory.get(f"{url}?search=COVID")
        force_authenticate(request, user=provider.user)

        view = MedicalRecordViewSet.as_view({"get": "list"})
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_create_record_provider_not_affiliated_with_hospital(
        self, provider_factory, patient_factory, hospital_factory, appointment_factory
    ):
        provider = provider_factory()
        patient = patient_factory()
        hospital = hospital_factory()
        appointment = appointment_factory(patient=patient, healthcare_provider=provider)

        data = {
            "patient_id": patient.user.id,
            "hospital_id": hospital.id,
            "appointment_id": appointment.id,
            "diagnosis": "Test diagnosis",
            "notes": "Test notes",
            "prescriptions": "Test prescriptions",
        }

        factory = APIRequestFactory()
        request = factory.post(reverse("medical_record-list"), data=data, format="json")
        force_authenticate(request, user=provider.user)

        view = MedicalRecordViewSet.as_view({"post": "create"})
        response = view(request)
        print(response.data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        error_messages = str(response.data["hospital_id"])
        assert "Provider is not affiliated with this hospital" in error_messages

    def test_update_record_provider_not_affiliated_with_new_hospital(
        self, medical_record_factory, hospital_factory, appointment_factory
    ):
        record = medical_record_factory()
        provider = record.healthcare_provider
        new_hospital = hospital_factory()
        appointment_factory()

        data = {"hospital_id": new_hospital.id, "diagnosis": "Updated diagnosis"}

        factory = APIRequestFactory()
        request = factory.patch(
            reverse("medical_record-detail", kwargs={"pk": record.id}),
            data=data,
            format="json",
        )
        force_authenticate(request, user=provider.user)

        view = MedicalRecordViewSet.as_view({"patch": "partial_update"})
        response = view(request, pk=record.id)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        error_messages = str(response.data["hospital_id"])
        assert "hospital" in error_messages

    def test_provider_cannot_create_record_for_themselves(
        self,
        healthcare_provider_factory,
        hospital_factory,
        patient_factory,
        appointment_factory,
    ):
        provider = healthcare_provider_factory()
        hospital = hospital_factory()
        patient = patient_factory(user=provider.user)
        appointment = appointment_factory(patient=patient, healthcare_provider=provider)

        ProviderHospitalAssignment.objects.create(
            healthcare_provider=provider,
            hospital=hospital,
            is_active=True,
            created_by=provider.user,
            updated_by=provider.user,
        )

        data = {
            "patient_id": patient.user.id,
            "hospital_id": hospital.id,
            "appointment_id": appointment.id,
            "diagnosis": "Self diagnosis",
            "notes": "Test notes",
            "prescriptions": "Test prescriptions",
        }

        factory = APIRequestFactory()
        request = factory.post(reverse("medical_record-list"), data=data, format="json")
        force_authenticate(request, user=provider.user)

        view = MedicalRecordViewSet.as_view({"post": "create"})
        response = view(request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "provider" in response.data or "patient" in response.data
