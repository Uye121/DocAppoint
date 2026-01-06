from rest_framework import serializers
from ..models import Hospital

class HospitalSerializer(serializers.ModelSerializer):
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