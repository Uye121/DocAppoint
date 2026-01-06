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
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        email = attrs.get("email")
        if email and User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                {"email": "A user with this email already exists."}
            )
        
        # Check password on create
        if self.instance is None:
            if not attrs.get('password'):
                raise serializers.ValidationError(
                    {"password": "Password is required."}
                )
        
        return attrs
        
    def create(self, validated_data):
        if not validated_data['password']:
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