# TODO: break up into respective file and delete
from typing import Any, Dict, List
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model

from mixin import CamelCaseMixin
from .utils.case import to_camelcase_data, to_snake_case_data, JsonValue
from .models import (
    Patient, HealthcareProvider, Appointment, 
    MedicalRecord, Message, Speciality, Hospital
)
    
class PatientSerializer(CamelCaseMixin, serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Patient
        fields = '__all__'
        
class HealthcareProviderSerializer(CamelCaseMixin, serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    speciality = serializers.StringRelatedField()
    
    class Meta:
        model = HealthcareProvider
        fields = '__all__'

class AppointmentSerializer(CamelCaseMixin, serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    healthcare_provider = HealthcareProviderSerializer(read_only=True)
    
    class Meta:
        model = Appointment
        fields = '__all__'

class MedicalRecordSerializer(CamelCaseMixin, serializers.ModelSerializer):
    class Meta:
        model = MedicalRecord
        fields = '__all__'

class MessageSerializer(CamelCaseMixin, serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    recipient = UserSerializer(read_only=True)
    
    class Meta:
        model = Message
        fields = '__all__'
        
class SpecialitySerializer(CamelCaseMixin, serializers.ModelSerializer):
    class Meta:
        model = Speciality
        fields = '__all__'

class HospitalSerializer(CamelCaseMixin, serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = '__all__'
