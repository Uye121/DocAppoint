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

pytestmark = pytest.mark.django_db(transaction=True)

class TestHealthcareProviderSerializer:
    def test_valid_update(self, provider_factory, speciality_factory):
        p = provider_factory(about="old", fees=Decimal("100.00"))
        s = speciality_factory()
        payload = {"about": "new", "fees": "150.00", "speciality": s.pk}
        ps = HealthcareProviderSerializer(instance=p, data=payload, partial=True)
        assert ps.is_valid(), ps.errors
        obj = ps.save()
        assert obj.about == "new"
        assert obj.fees == Decimal("150.00")

    def test_speciality_required(self, provider_factory):
        p = provider_factory()
        payload = {"speciality": None}
        ps = HealthcareProviderSerializer(instance=p, data=payload, partial=True)
        assert not ps.is_valid()
        assert "speciality" in ps.errors

    def test_fees_invalid(self, provider_factory):
        p = provider_factory()
        ps = HealthcareProviderSerializer(instance=p, data={"fees": 9999999999}, partial=True)
        assert not ps.is_valid()
        assert "fees" in ps.errors

    def test_license_bad_format(self, provider_factory):
        p = provider_factory()
        ps = HealthcareProviderSerializer(instance=p, data={"license_number": "abc"}, partial=True)
        assert not ps.is_valid()
        assert "license_number" in ps.errors

class TestHealthcareProviderCreateSerializer:
    @pytest.fixture
    def base_payload(self):
        def _payload(**overrides):
            payload = {
                "email": "doc@test.com",
                "username": "docnew",
                "password": "Complex123!",
                "first_name": "Doc",
                "last_name": "Tor",
                "speciality": None,
                "fees": "120.00",
                "address_line1": "123 Main",
                "city": "Town",
                "state": "CA",
                "zip_code": "12345",
                "license_number": "AB123456",
            }
            payload.update(overrides)
            return payload
        return _payload

    def test_create(self, base_payload, speciality_factory):
        sp = speciality_factory()
        payload = base_payload(speciality=sp.pk)
        ser = HealthcareProviderCreateSerializer(data=payload)
        assert ser.is_valid(), ser.errors
        obj = ser.save()
        assert obj.user.email == "doc@test.com"
        assert obj.fees == Decimal("120.00")
        assert obj.years_of_experience == 0 
        assert obj.user.check_password("Complex123!")

    def test_email_case_insensitive_duplicate(
        self,
        base_payload,
        user_factory,
        speciality_factory
    ):
        user_factory(email="doc@test.com")
        payload = base_payload(
            speciality=speciality_factory().pk,
        )
        ps = HealthcareProviderCreateSerializer(data=payload)
        assert not ps.is_valid()
        assert "email" in ps.errors

    def test_speciality_missing(self, base_payload):
        payload = base_payload()
        ps = HealthcareProviderCreateSerializer(data=payload)
        assert not ps.is_valid()
        assert "speciality" in ps.errors

    def test_invalid_license(self, base_payload, speciality_factory):
        sp = speciality_factory()
        payload = base_payload(license_number="12", speciality=sp.pk)
        ps = HealthcareProviderCreateSerializer(data=payload)
        assert not ps.is_valid()
        assert "license_number" in ps.errors

    def test_password_blank_invalid(self, base_payload, speciality_factory):
        sp = speciality_factory()
        payload = base_payload(password="")
        ps = HealthcareProviderCreateSerializer(data=payload)
        assert not ps.is_valid()
        assert "password" in ps.errors

class TestHealthcareProviderListSerializer:
    def test_list(self, provider_factory):
        p = provider_factory()
        ps = HealthcareProviderListSerializer(instance=p)
        data = ps.data
        assert data["specialityName"] == p.speciality.name
        assert data["firstName"] == p.user.first_name
        assert data["lastName"] == p.user.last_name

class TestHealthcareProviderOnBoardSerializer:
    @pytest.fixture
    def base_payload(self):
        def _payload(**overrides):
            payload = {
                "email": "doc@test.com",
                "username": "docnew",
                "password": "Complex123!",
                "first_name": "Doc",
                "last_name": "Tor",
                "speciality": None,
                "about": "test",
                "fees": "120.00",
                "address_line1": "123 Main",
                "city": "Town",
                "state": "CA",
                "zip_code": "12345",
                "license_number": "AB123456",
            }
            payload.update(overrides)
            return payload
        return _payload
    
    def test_create_first_time(
        self,
        rf,
        base_payload,
        user_factory,
        speciality_factory
    ):
        user = user_factory()
        request = rf.post("/fake/")
        payload = base_payload(
            user=user.pk,
            fees="99.99",
            speciality=speciality_factory().pk
        )
        ps = HealthcareProviderOnBoardSerializer(data=payload, context={"request": request})
        assert ps.is_valid(), ps.errors
        obj = ps.save()
        assert obj.user == user
        assert obj.fees == Decimal("99.99")

    def test_second_provider(
        self,
        rf,
        base_payload,
        provider_factory,
        speciality_factory
    ):
        p = provider_factory()
        request = rf.post("/fake/")
        payload = base_payload(
            user=p.user.pk,
            speciality=speciality_factory().pk
        )
        ps = HealthcareProviderOnBoardSerializer(data=payload, context={"request": request})
        assert not ps.is_valid()
        assert "already exists" in str(ps.errors)

    def test_fees_negative(
        self,
        rf,
        base_payload,
        user_factory,
        speciality_factory
    ):
        user = user_factory()
        request = rf.post("/fake/")
        payload = base_payload(user=user.pk, speciality=speciality_factory().pk, fees=-10)
        ps = HealthcareProviderOnBoardSerializer(data=payload, context={"request": request})
        assert not ps.is_valid()
        assert "fees" in ps.errors