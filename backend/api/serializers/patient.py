from rest_framework import serializers
from django.contrib.auth import password_validation

from ..models import User, Patient
from ..mixin import CamelCaseMixin
from .user import UserSerializer

class PatientSerializer(CamelCaseMixin, serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Patient
        fields = [
            "user",
            "blood_type",
            "allergies",
            "chronic_conditions",
            "current_medications",
            "insurance",
            "weight",
            "height",
        ]

    def validate(self, attrs):
        """Checks for PATCH/PUT."""
        wt = attrs.get("weight")
        if wt is not None and wt <= 0:
            raise serializers.ValidationError({"weight": "Must be a positive number (kg)."})

        ht = attrs.get("height")
        if ht is not None and ht <= 0:
            raise serializers.ValidationError({"height": "Must be a positive number (cm)."})

        return attrs

class PatientCreateSerializer(CamelCaseMixin, serializers.ModelSerializer):
    """
    Used for *standalone* patient creation (user + patient profile in one call).
    """
    # user fields
    email = serializers.EmailField(write_only=True)
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, validators=[password_validation.validate_password])
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    image = serializers.ImageField(required=False, allow_null=True)

    # patient specific fields
    blood_type = serializers.CharField(required=False, allow_blank=True)
    allergies = serializers.CharField(required=False, allow_blank=True)
    chronic_conditions = serializers.CharField(required=False, allow_blank=True)
    current_medications = serializers.CharField(required=False, allow_blank=True)
    insurance = serializers.CharField(required=False, allow_blank=True)
    weight = serializers.IntegerField(required=False, allow_null=True)
    height = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = Patient
        fields = [
            # user part
            "email",
            "username",
            "password",
            "first_name",
            "last_name",
            "date_of_birth",
            "image",
            # patient part
            "blood_type",
            "allergies",
            "chronic_conditions",
            "current_medications",
            "insurance",
            "weight",
            "height",
        ]

    def validate(self, attrs):
        email = attrs.get("email")
        if email and User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                {"email": "A user with this email already exists."}
            )

        wt = attrs.get("weight")
        if wt is not None and wt <= 0:
            raise serializers.ValidationError(
                {"weight": "Must be a positive number (kg)."}
            )

        ht = attrs.get("height")
        if ht is not None and ht <= 0:
            raise serializers.ValidationError(
                {"height": "Must be a positive number (cm)."}
            )

        return attrs

    def create(self, validated_data):
        if not validated_data['password']:
            raise serializers.ValidationError({"password": "Password cannot be blank."})

        user_data = {
            k: validated_data.pop(k, None)
            for k in (
                "email",
                "username",
                "first_name",
                "last_name",
                "password",
                "date_of_birth",
                "image",
            )
        }

        user = User.objects.create_user(**user_data, is_active=False)
        patient = Patient.objects.create(user=user, **validated_data)
        return patient

class PatientOnBoardSerializer(CamelCaseMixin, serializers.ModelSerializer):
    """
    Turn existing user into a patient with PATCH or POST
    """
    class Meta:
        model = Patient
        fields = [
            "blood_type",
            "allergies",
            "chronic_conditions",
            "current_medications",
            "insurance",
            "weight",
            "height",
        ]

    def validate(self, attrs):
        wt = attrs.get("weight")
        if wt is not None and wt <= 0:
            raise serializers.ValidationError({"weight": "Must be a positive number (kg)."})

        ht = attrs.get("height")
        if ht is not None and ht <= 0:
            raise serializers.ValidationError({"height": "Must be a positive number (cm)."})

        user = self.context["request"].user
        # Check for existing user only during create
        if self.instance is None:
            if hasattr(user, "patient"):
                raise serializers.ValidationError(
                    "Patient profile already exists."
                )

        return attrs

    def create(self, validated_data):
        return Patient.objects.create(user=self.context["request"].user, **validated_data)

    def update(self, instance, validated_data):
        # in case patient row already exists
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        return instance
