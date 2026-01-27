from rest_framework import serializers
from ..models import Hospital
from ..mixin import CamelCaseMixin


class HospitalSerializer(CamelCaseMixin, serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = (
            "id",
            "name",
            "address",
            "phone_number",
            "timezone",
            "is_removed",
            "removed_at",
        )
        read_only_fields = ("id", "is_removed", "removed_at")
