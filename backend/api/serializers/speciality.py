from rest_framework import serializers

from ..models import Speciality

class SpecialitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Speciality
        fields = (
            "id",
            "name",
            "image",
            "is_removed",
            "removed_at",
            "created_by",
            "updated_by"
        )
        read_only_fields = ("id", "created_at", "updated_by", "is_removed", "removed_at")

class SpecialityListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Speciality
        fields = (
            "id",
            "name",
            "image",
        )

# Used for creating new specialities
class SpecialityCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Speciality
        fields = (
            "name",
            "image",
        )
