from rest_framework import serializers
from django.contrib.auth import password_validation

from ..models import User, AdminStaff, Hospital
from ..mixin import CamelCaseMixin
from .user import UserSerializer


class AdminStaffSerializer(CamelCaseMixin, serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    hospital_name = serializers.CharField(source="hospital.name", read_only=True)

    class Meta:
        model = AdminStaff
        fields = ["user", "hospital", "hospital_name"]


class AdminStaffCreateSerializer(CamelCaseMixin, serializers.ModelSerializer):
    email = serializers.EmailField()
    username = serializers.CharField()
    password = serializers.CharField(
        write_only=True, validators=[password_validation.validate_password]
    )
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    image = serializers.ImageField(required=False, allow_null=True)

    # admin-staff
    hospital = serializers.PrimaryKeyRelatedField(queryset=Hospital.objects.all())

    class Meta:
        model = AdminStaff
        fields = [
            "email",
            "username",
            "password",
            "first_name",
            "last_name",
            "date_of_birth",
            "image",
            "hospital",
        ]

    def validate(self, attrs):
        email = attrs.get("email")
        if email and User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                {"email": "A user with this email already exists."}
            )

        return attrs

    def create(self, validated_data):
        if not validated_data["password"]:
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
        admin_staff = AdminStaff.objects.create(user=user, **validated_data)
        return admin_staff


class AdminStaffOnBoardSerializer(CamelCaseMixin, serializers.ModelSerializer):
    """
    Turn existing user into a admin staff with PATCH or POST
    """

    class Meta:
        model = AdminStaff
        fields = ["hospital"]

    def validate(self, attrs):
        if not attrs.get("hospital"):
            raise serializers.ValidationError(
                {"hospital": "Hospital affiliation is required."}
            )

        user = self.context["request"].user
        # Check for existing user only during create
        if self.instance is None:
            if hasattr(user, "admin_staff"):
                raise serializers.ValidationError("Admin staff profile already exists.")

        return attrs

    def create(self, validated_data):
        user = self.context["request"].user
        return AdminStaff.objects.create(user=user, **validated_data)

    def update(self, instance, validated_data):
        # in case admin staff row already exists
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        return instance
