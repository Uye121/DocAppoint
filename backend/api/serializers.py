from typing import Any, Dict, List
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    User, Patient, HealthcareProvider, Appointment, 
    MedicalRecord, Message, Speciality, Hospital
)
from .utils.case import to_camelcase_data, to_snake_case_data, JsonValue

class CamelCaseMixin:
    def to_representation(self, instance: Any) -> Dict[str, Any]:
        representation = super().to_representation(instance) # type: ignore
        return to_camelcase_data(representation) # type: ignore

    def to_internal_value(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return super().to_internal_value(to_snake_case_data(data)) # type: ignore

class UserSerializer(CamelCaseMixin, serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'type', 
                 'date_of_birth', 'phone_number', 'address']
        extra_kwargs = {'password': {'write_only': True}}
    
    def create(self, validated_data: dict[str, Any]) -> User:
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user    
    
class PatientSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Patient
        fields = '__all__'
        
class HealthcareProviderSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    speciality = serializers.StringRelatedField()
    
    class Meta:
        model = HealthcareProvider
        fields = '__all__'

class AppointmentSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    healthcare_provider = HealthcareProviderSerializer(read_only=True)
    
    class Meta:
        model = Appointment
        fields = '__all__'

class MedicalRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalRecord
        fields = '__all__'

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    recipient = UserSerializer(read_only=True)
    
    class Meta:
        model = Message
        fields = '__all__'
        
class SpecialitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Speciality
        fields = '__all__'

class HospitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = '__all__'
