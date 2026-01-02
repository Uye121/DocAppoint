import logging
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password

from ..mixin import CamelCaseMixin

logger = logging.getLogger(__name__)

class ChangePasswordSerializer(CamelCaseMixin, serializers.Serializer):
    old_password = serializers.CharField(required=True, style={"input_type": "password"})
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password],
        style={"input_type": "password"}
    )

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"}
    )

    def validate(self, attrs):
        email = attrs.get("email").strip().lower()
        password = attrs.get("password")

        if email and password:
            user = authenticate(
                request=self.context.get("request"),
                username=email,
                password=password
            )

            if not user:
                raise serializers.ValidationError(
                    "Invalid email/password pair.", code="authorization"
                )
            if not user.is_active:
                raise serializers.ValidationError(
                    "Account is not active.", code="authorization"
                )
        else:
            raise serializers.ValidationError(
                "Email and password are required.", code="authorization"
            )
        
        attrs["user"] = user
        return attrs
