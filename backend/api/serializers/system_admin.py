from rest_framework import serializers
from django.contrib.auth import password_validation

from ..models import User, SystemAdmin
from ..mixin import CamelCaseMixin
from .user import UserSerializer


class SystemAdminSerializer(CamelCaseMixin, serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = SystemAdmin
        fields = ["user", "role"]


class SystemAdminCreateSerializer(CamelCaseMixin, serializers.ModelSerializer):
    # user
    email = serializers.EmailField()
    username = serializers.CharField()
    password = serializers.CharField(
        write_only=True, validators=[password_validation.validate_password]
    )
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    image = serializers.ImageField(required=False, allow_null=True)

    # system-admin
    role = serializers.CharField()

    class Meta:
        model = SystemAdmin
        fields = [
            "email",
            "username",
            "password",
            "first_name",
            "last_name",
            "date_of_birth",
            "image",
            "role",
        ]

    def validate(self, attrs):
        email = attrs.get("email")
        if email and User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                {"email": "A user with this email already exists."}
            )

        role = attrs.get("role")
        if not role or role.strip() == "":
            raise serializers.ValidationError({"role": "Role is required."})

        return attrs

    def create(self, validated_data):
        user_data = {
            k: validated_data.pop(k, None)
            for k in (
                "email",
                "username",
                "password",
                "first_name",
                "last_name",
                "date_of_birth",
                "image",
            )
        }

        user = User.objects.create_user(**user_data, is_active=False, is_staff=True)
        sys_admin = SystemAdmin.objects.create(user=user, **validated_data)
        return sys_admin


class SystemAdminOnBoardSerializer(CamelCaseMixin, serializers.ModelSerializer):
    """
    Turn existing user into a system admin with PATCH or POST
    """

    class Meta:
        model = SystemAdmin
        fields = ["role"]

    def validate(self, attrs):
        role = attrs.get("role")
        if not role or role.strip() == "":
            raise serializers.ValidationError({"role": "Role is required."})

        user = self.context["request"].user
        # Check for existing user only during create
        if self.instance is None:
            if hasattr(user, "system_admin"):
                raise serializers.ValidationError(
                    "You are already registered as a system admin."
                )

        return attrs

    def create(self, validated_data):
        user = self.context["request"].user
        user.is_staff = True
        user.save()
        return SystemAdmin.objects.create(user=user, **validated_data)

    def update(self, instance, validated_data):
        # in case system admin row already exists
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        return instance
