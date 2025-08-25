from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Speciality, Doctor
from .utils.case import to_camelcase_data, to_snake_case_data

User = get_user_model()

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "name", "password"]
        extra_kwargs = { "password": {"write_only": True} }
        
    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data["email"],
            name=validated_data["name"],
            password=validated_data["password"],
        )
        return user

class SpecialitySerializer(serializers.ModelSerializer):
    def validate_name(self, value):
        """
        Check if speicality with the same name already exist

        Args:
            value (str): name of the speciality
        """
        if Speciality.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError(f"A speciality with the name {value} already exists.")
        return value
    
    class Meta:
        model = Speciality
        fields = ["id", "name", "image"]

class CamelCaseMixin:
    def to_representation(self, *args, **kwargs):
        return to_camelcase_data(super().to_representation(*args, **kwargs))

    def to_internal_value(self, data):
        return super().to_internal_value(to_snake_case_data(data))

class DoctorSerializer(CamelCaseMixin, serializers.ModelSerializer):
    speciality = SpecialitySerializer(read_only=True)
    
    class Meta:
        model = Doctor
        fields = [
            "id",
            "first_name", 
            "last_name",
            "image",
            "speciality",
            "degree",
            "experience",
            "about",
            "fees",
            "address_line1",
            "address_line2",
        ]
