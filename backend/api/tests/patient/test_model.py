import pytest
from django.contrib.auth import get_user_model

User = get_user_model()

pytestmark = pytest.mark.django_db(transaction=True)

def test_patient_one_to_one_relation(patient_factory, user_factory):
    u = user_factory()
    p = patient_factory(user=u)
    assert u.patient == p
    assert p.user == u