from rest_framework import serializers
from ..models import HealthcareProviderProfile
from ..mixin import CamelCaseMixin

class HealthcareProviderProfileSerializer(CamelCaseMixin, serializers.ModelSerializer):
    speciality_name = serializers.CharField(source='speciality.name', read_only=True)
    primary_hospital_name = serializers.CharField(source='primary_hospital.name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)

    class Meta:
        model = HealthcareProviderProfile
        fields = (
            "id",
            "username",
            "first_name",
            "last_name", 
            "speciality",
            "speciality_name", 
            "image",
            "education",
            "years_of_experience",
            "about",
            "fees",
            "address_line1",
            "address_line2",
            "city",
            "state",
            "zip_code",
            "license_number",
            "certifications",
            "primary_hospital",
            "primary_hospital_name",
            "is_removed",
            "removed_at",
            "created_by",
            "updated_by",
        )
        read_only_fields = (
            "id", "created_by", "updated_by", "is_removed", "removed_at",
            "email", "username", "first_name", "last_name", "speciality_name", "primary_hospital_name"
        )

class HealthcareProviderProfileCreateSerializer(CamelCaseMixin, serializers.ModelSerializer):
    class Meta:
        model = HealthcareProviderProfile
        fields = (
            "speciality",
            "image",
            "education", 
            "years_of_experience",
            "about",
            "fees",
            "address_line1",
            "address_line2",
            "city",
            "state",
            "zip_code",
            "license_number",
            "certifications",
            "primary_hospital",
        )

class HealthcareProviderListSerializer(serializers.ModelSerializer):
    speciality_name = serializers.CharField(source='speciality.name', read_only=True)
    primary_hospital_name = serializers.CharField(source='primary_hospital.name', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    rating = serializers.SerializerMethodField()

    class Meta:
        model = HealthcareProviderProfile
        fields = (
            "id",
            "full_name",
            "speciality",
            "speciality_name", 
            "image",
            "years_of_experience",
            "fees",
            "primary_hospital",
            "primary_hospital_name",
            "rating",
        )

    def get_rating(self, obj):
        return 5.0
