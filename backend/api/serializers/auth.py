import logging
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from rest_framework.response import Response

from ..mixin import CamelCaseMixin
from ..models import User

logger = logging.getLogger(__name__)

class SignUpSerializer(CamelCaseMixin, serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = (
            "email",
            "username",
            "password",
            "first_name",
            "last_name",
        )
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        valid_data = serializer.is_valid()
        if not valid_data:
            logger.error('validation errors →', serializer.errors)
            return Response(serializer.errors, status=400)
        return super().post(request, *args, **kwargs)

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        user.is_active = False 
        user.save()
        return user

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])

class UserSerializer(CamelCaseMixin, serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'type', 
                 'date_of_birth', 'phone_number', 'address']
        extra_kwargs = {'password': {'write_only': True}}
        read_only_fields = fields
