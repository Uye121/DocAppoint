import os
import pytest
from django.contrib.auth import get_user_model

from ...serializers import (
    PatientSerializer,
    PatientCreateSerializer,
    PatientOnBoardSerializer,
)

User = get_user_model()

pytestmark = pytest.mark.django_db(transaction=True)

class TestPatientSerializer:
    def setup_method(self):
        self.temp_files = []
    
    def teardown_method(self):
        # Clean up any temporary files
        for file_path in self.temp_files:
            if os.path.exists(file_path):
                os.remove(file_path)
    def test_valid_payload(self, patient_factory):
        p = patient_factory(weight=70, height=180)
        payload = {"weight": 75, "height": 185}
        ps = PatientSerializer(instance=p, data=payload, partial=True)
        assert ps.is_valid(), ps.errors
        obj = ps.save()
        assert obj.weight == 75
        assert obj.height == 185

    def test_weight_zero_invalid(self, patient_factory):
        p = patient_factory()
        ps = PatientSerializer(instance=p, data={"weight": 0}, partial=True)
        assert not ps.is_valid()
        assert "weight" in ps.errors

    def test_height_negative_invalid(self, patient_factory):
        p = patient_factory()
        ps = PatientSerializer(instance=p, data={"height": -10}, partial=True)
        assert not ps.is_valid()
        assert "height" in ps.errors

class TestPatientCreateSerializer:
    @pytest.fixture
    def base_payload(self):
        def _payload(**overrides):
            payload = {
                "email": "new@patient.com",
                "username": "newpatient",
                "password": "Complex123!",
                "first_name": "Neo",
                "last_name": "Patient",
                "date_of_birth": "1990-01-01",
                "blood_type": "O+",
                "weight": 80,
                "height": 190,
            }
            payload.update(overrides)
            return payload
        return _payload
    
    def test_create_full(self, base_payload):
        assert User.objects.count() == 0
        payload = base_payload()
        ps = PatientCreateSerializer(data=payload)
        assert ps.is_valid(), ps.errors
        patient = ps.save()
        assert User.objects.count() == 1
        assert patient.user.email == "new@patient.com"
        assert patient.weight == 80

    def test_email_case_insensitive_duplicate(self, base_payload, user_factory):
        user_factory(email="NEW@patient.com")
        payload = base_payload()
        ps = PatientCreateSerializer(data=payload)
        assert not ps.is_valid()
        assert "email" in ps.errors

    def test_weight_zero_rejected(self, base_payload):
        payload = base_payload(weight=0)
        ps = PatientCreateSerializer(data=payload)
        assert not ps.is_valid()
        assert "weight" in ps.errors

class TestPatientOnBoardSerializer:
    def setup(self, user_factory):
        self.user = user_factory()

    def test_create_first_time(self, rf, user_factory):
        user = user_factory()
        request = rf.post("/fake/")
        request.user = user
        payload = {"weight": 70, "height": 175}
        ps = PatientOnBoardSerializer(data=payload, context={"request": request})
        assert ps.is_valid(), ps.errors
        patient = ps.save()
        assert patient.user == user
        assert patient.weight == 70

    def test_second_profile_rejected(self, rf, patient_factory):
        p = patient_factory()
        request = rf.post("/fake/")
        request.user = p.user
        payload = {"weight": 80}
        ps = PatientOnBoardSerializer(data=payload, context={"request": request})
        assert not ps.is_valid()
        assert "Patient profile already exists." in str(ps.errors)

    def test_height_negative_rejected(self, rf, user_factory):
        user = user_factory()
        request = rf.post("/fake/")
        request.user = user
        payload = {"height": -5}
        ps = PatientOnBoardSerializer(data=payload, context={"request": request})
        assert not ps.is_valid()
        assert "height" in ps.errors
