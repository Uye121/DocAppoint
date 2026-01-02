import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model

from ...serializers import (
    HealthcareProviderSerializer,
    HealthcareProviderCreateSerializer,
    HealthcareProviderListSerializer,
    HealthcareProviderOnBoardSerializer,
)

User = get_user_model()

pytestmark = pytest.mark.django_db

class TestHealthcareProviderSerializer:
    def test_valid_update(self, healthcare_provider_factory, speciality_factory):
        p = healthcare_provider_factory(about="old", fees=Decimal("100.00"))
        s = speciality_factory()
        payload = {"about": "new", "fees": "150.00", "speciality": s.pk}
        ps = HealthcareProviderSerializer(instance=p, data=payload, partial=True)
        assert ps.is_valid(), ps.errors
        obj = ps.save()
        assert obj.about == "new"
        assert obj.fees == Decimal("150.00")

    def test_speciality_required(self, healthcare_provider_factory):
        p = healthcare_provider_factory()
        payload = {"speciality": None}
        ps = HealthcareProviderSerializer(instance=p, data=payload, partial=True)
        assert not ps.is_valid()
        assert "speciality" in ps.errors

    def test_fees_invalid(self, healthcare_provider_factory):
        p = healthcare_provider_factory()
        ps = HealthcareProviderSerializer(instance=p, data={"fees": 9999999999}, partial=True)
        assert not ps.is_valid()
        assert "fees" in ps.errors

    def test_license_bad_format(self, healthcare_provider_factory):
        p = healthcare_provider_factory()
        ps = HealthcareProviderSerializer(instance=p, data={"license_number": "abc"}, partial=True)
        assert not ps.is_valid()
        assert "license_number" in ps.errors

class TestHealthcareProviderCreateSerializer:
    def test_create(self, speciality_factory):
        sp = speciality_factory()
        payload = {
            "email": "doc@new.com",
            "username": "docnew",
            "password": "Complex123!",
            "first_name": "Doc",
            "last_name": "Tor",
            "speciality": sp.pk,
            "fees": "120.00",
            "address_line1": "123 Main",
            "city": "Town",
            "state": "CA",
            "zip_code": "12345",
            "license_number": "AB123456",
        }
        ser = HealthcareProviderCreateSerializer(data=payload)
        assert ser.is_valid(), ser.errors
        obj = ser.save()
        assert obj.user.email == "doc@new.com"
        assert obj.fees == Decimal("120.00")
        assert obj.years_of_experience == 0 
        assert obj.user.check_password("Complex123!")

    def test_email_case_insensitive_duplicate(self, user_factory, speciality_factory):
        user_factory(email="EXIST@example.com")
        payload = {
            "email": "exist@example.com",
            "username": "doc",
            "password": "Complex123!",
            "first_name": "A",
            "last_name": "B",
            "speciality": speciality_factory().pk,
            "fees": "100.00",
            "address_line1": "123 Main",
            "city": "Town",
            "state": "CA",
            "zip_code": "12345",
            "license_number": "AB123456",
        }
        ps = HealthcareProviderCreateSerializer(data=payload)
        assert not ps.is_valid()
        assert "email" in ps.errors

    def test_speciality_missing(self):
        payload = {
            "email": "doc@new.com",
            "username": "doc",
            "password": "Complex123!",
            "first_name": "A",
            "last_name": "B",
            "fees": "100.00",
            "address_line1": "123 Main",
            "city": "Town",
            "state": "CA",
            "zip_code": "12345",
            "license_number": "AB123456",
        }
        ps = HealthcareProviderCreateSerializer(data=payload)
        assert not ps.is_valid()
        assert "speciality" in ps.errors

    def test_invalid_license(self, speciality_factory):
        sp = speciality_factory()
        payload = {
            "email": "doc@new.com",
            "username": "doc",
            "password": "Complex123!",
            "first_name": "A",
            "last_name": "B",
            "speciality": sp.pk,
            "fees": "100.00",
            "address_line1": "123 Main",
            "city": "Town",
            "state": "CA",
            "zip_code": "12345",
            "license_number": "12",
        }
        ps = HealthcareProviderCreateSerializer(data=payload)
        assert not ps.is_valid()
        assert "license_number" in ps.errors

    def test_password_blank_invalid(self, speciality_factory):
        sp = speciality_factory()
        payload = {
            "email": "doc@new.com",
            "username": "doc",
            "password": "",
            "first_name": "A",
            "last_name": "B",
            "speciality": sp.pk,
            "fees": "100.00",
            "address_line1": "123 Main",
            "city": "Town",
            "state": "CA",
            "zip_code": "12345",
            "license_number": "AB123456",
        }
        ps = HealthcareProviderCreateSerializer(data=payload)
        assert not ps.is_valid()
        assert "password" in ps.errors

class TestHealthcareProviderListSerializer:
    def test_list(self, healthcare_provider_factory):
        p = healthcare_provider_factory()
        ps = HealthcareProviderListSerializer(instance=p)
        data = ps.data
        assert data["specialityName"] == p.speciality.name
        assert data["primaryHospitalName"] == p.primary_hospital.name
        assert data["firstName"] == p.user.first_name
        assert data["lastName"] == p.user.last_name

class TestHealthcareProviderOnBoardSerializer:
    def test_create_first_time(self, rf, user_factory, speciality_factory):
        user = user_factory()
        request = rf.post("/fake/")
        payload = {
            "user": user.pk,
            "about": "test",
            "speciality": speciality_factory().pk,
            "fees": "99.99",
            "address_line1": "456 Oak",
            "city": "Ville",
            "state": "NY",
            "zip_code": "54321",
            "license_number": "XY987654",
        }
        ps = HealthcareProviderOnBoardSerializer(data=payload, context={"request": request})
        assert ps.is_valid(), ps.errors
        obj = ps.save()
        assert obj.user == user
        assert obj.fees == Decimal("99.99")

    def test_second_provider(self, rf, healthcare_provider_factory, speciality_factory):
        p = healthcare_provider_factory()
        request = rf.post("/fake/")
        payload = {
            "user": p.user.pk,
            "about": "test",
            "speciality": speciality_factory().pk,
            "fees": "99.99",
            "address_line1": "456 Oak",
            "city": "Ville",
            "state": "NY",
            "zip_code": "54321",
            "license_number": "XY987654",
        }
        ps = HealthcareProviderOnBoardSerializer(data=payload, context={"request": request})
        assert not ps.is_valid()
        assert "already exists" in str(ps.errors)

    def test_fees_negative(self, rf, user_factory, speciality_factory):
        user = user_factory()
        request = rf.post("/fake/")
        payload = {
            "user": user.pk,
            "about": "test",
            "speciality": speciality_factory().pk,
            "fees": -10,
            "address_line1": "456 Oak",
            "city": "Ville",
            "state": "NY",
            "zip_code": "54321",
            "license_number": "XY987654",
        }
        ps = HealthcareProviderOnBoardSerializer(data=payload, context={"request": request})
        assert not ps.is_valid()
        assert "fees" in ps.errors