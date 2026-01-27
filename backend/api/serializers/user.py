from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from ..mixin import CamelCaseMixin

User = get_user_model()


class UserSerializer(CamelCaseMixin, serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=False,
        validators=[validate_password],
    )
    has_patient_profile = serializers.SerializerMethodField()
    has_provider_profile = serializers.SerializerMethodField()
    has_admin_staff_profile = serializers.SerializerMethodField()
    has_system_admin_profile = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "date_of_birth",
            "phone_number",
            "address",
            "image",
            "password",
            "has_patient_profile",
            "has_provider_profile",
            "has_admin_staff_profile",
            "has_system_admin_profile",
            "user_role",
        ]
        read_only_fields = ["id"]

    def get_has_patient_profile(self, obj):
        return hasattr(obj, "patient")

    def get_has_provider_profile(self, obj):
        return hasattr(obj, "provider")

    def get_has_admin_staff_profile(self, obj):
        return hasattr(obj, "admin_staff")

    def get_has_system_admin_profile(self, obj):
        return hasattr(obj, "system_admin")

    def get_user_role(self, obj):
        """Determine primary role based on hierarchy"""
        if hasattr(obj, "system_admin"):
            return "system_admin"
        elif hasattr(obj, "admin_staff"):
            return "admin_staff"
        elif hasattr(obj, "provider"):
            return "provider"
        elif hasattr(obj, "patient"):
            return "patient"
        return "unassigned"

    def validate(self, attrs):
        email = attrs.get("email")
        if email and User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                {"email": "A user with this email already exists."}
            )

        # Check password on create
        if self.instance is None:
            if not attrs.get("password"):
                raise serializers.ValidationError({"password": "Password is required."})

        return attrs

    def create(self, validated_data):
        if not validated_data["password"]:
            raise serializers.ValidationError({"password": "Password cannot be blank."})

        user = User.objects.create_user(**validated_data, is_active=False)
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
