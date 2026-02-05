from rest_framework import serializers
from ..models import Hospital
from ..mixin import CamelCaseMixin


class HospitalSerializer(CamelCaseMixin, serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = (
            "id",
            "name",
            "address_line1",
            "address_line2",
            "phone_number",
            "timezone",
            "is_removed",
            "removed_at",
        )
        read_only_fields = ("id", "is_removed", "removed_at")


class HospitalTinySerializer(CamelCaseMixin, serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = ("id", "name", "address_line1", "address_line2", "timezone")
