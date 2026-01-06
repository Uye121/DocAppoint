import re
from rest_framework import serializers
from django.contrib.auth import password_validation

from ..models import HealthcareProvider, Speciality, Hospital, User
from ..mixin import CamelCaseMixin
from .user import UserSerializer

class HealthcareProviderSerializer(CamelCaseMixin, serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(source='user', read_only=True)
    user = UserSerializer(read_only=True)
    speciality_name = serializers.CharField(source='speciality.name', read_only=True)

    class Meta:
        model = HealthcareProvider
        fields = [
            "id",
            "user",
            "speciality",
            "speciality_name", 
            "education",
            "years_of_experience",
            "about",
            "fees",
            "address_line1",
            "address_line2",
            "city",
            "state",
            "zip_code",
            "license_number",
            "certifications",
            "primary_hospital",
            "hospitals",
            "is_removed",
            "removed_at",
        ]
        read_only_fields = ["removed_at"]

    def validate(self, attrs):
        # Check for speciality set to None
        if 'speciality' in attrs and attrs['speciality'] is None:
            raise serializers.ValidationError(
                {'speciality': 'Speciality is required.'}
            )
        
        # Require speciality for full updates (PUT), but not partial updates (PATCH)
        if not self.partial and 'speciality' not in attrs:
            raise serializers.ValidationError(
                {'speciality': 'Speciality is required.'}
            )
        
        fees = attrs.get('fees')
        if fees and fees <= 0:
            raise serializers.ValidationError(
                {'fees': 'Fees must be greater than zero.'}
            )

        lic = attrs.get('license_number')
        if lic and not re.match(r'^[A-Z0-9]{6,20}$', lic):
            raise serializers.ValidationError(
                {'license_number': '6-20 alphanumeric characters required.'}
            )

        return attrs

class HealthcareProviderCreateSerializer(CamelCaseMixin, serializers.ModelSerializer):
    # user fields
    email = serializers.EmailField(write_only=True)
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, validators=[password_validation.validate_password])
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    image = serializers.ImageField(required=False, allow_null=True)

    # provider fields
    speciality = serializers.PrimaryKeyRelatedField(queryset=Speciality.objects.all())
    education = serializers.CharField(required=False, allow_blank=True)
    years_of_experience = serializers.IntegerField(min_value=0, default=0)
    about = serializers.CharField(required=False, allow_blank=True)
    fees = serializers.DecimalField(max_digits=9, decimal_places=2)
    address_line1 = serializers.CharField()
    address_line2 = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(write_only=True)
    state = serializers.CharField(write_only=True)
    zip_code = serializers.CharField(write_only=True)
    license_number = serializers.CharField(write_only=True)
    certifications = serializers.CharField(required=False, allow_blank=True)
    primary_hospital = serializers.PrimaryKeyRelatedField(
        queryset=Hospital.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = HealthcareProvider
        fields = [
            "email",
            "username",
            "password",
            "first_name",
            "last_name",
            "date_of_birth",
            "image",
            "speciality",
            "education", 
            "years_of_experience",
            "about",
            "fees",
            "address_line1",
            "address_line2",
            "city",
            "state",
            "zip_code",
            "license_number",
            "certifications",
            "primary_hospital",
        ]

    def validate(self, attrs):
        email = attrs.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                {'email': 'A user with this email already exists.'}
            )
        
        if not attrs.get('speciality'):
            raise serializers.ValidationError(
                {'speciality': 'Speciality is required.'}
            )
        
        fees = attrs.get('fees')
        if fees is not None and fees <= 0:
            raise serializers.ValidationError(
                {'fees': 'Fees must be greater than zero.'}
            )

        lic = attrs.get('license_number')
        if lic and not re.match(r'^[A-Z0-9]{6,20}$', lic):
            raise serializers.ValidationError(
                {'license_number': '6-20 alphanumeric characters required.'}
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
        provider = HealthcareProvider.objects.create(user=user, **validated_data)
        return provider

class HealthcareProviderListSerializer(CamelCaseMixin, serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(source='user', read_only=True)
    speciality_name = serializers.CharField(source='speciality.name', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    image = serializers.ImageField(source='user.image', read_only=True)

    class Meta:
        model = HealthcareProvider
        fields = [
            "id",
            "speciality",
            "speciality_name", 
            "first_name",
            "last_name",
            "image"
        ]

class HealthcareProviderOnBoardSerializer(CamelCaseMixin, serializers.ModelSerializer):
    """
    Turn existing user into a Healthcare provider with PATCH or POST
    """
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=True,
        help_text="User ID to onboard."
    )
    about = serializers.CharField(required=True) 

    class Meta:
        model = HealthcareProvider
        fields = [
            "user",
            "speciality",
            "education", 
            "years_of_experience",
            "about",
            "fees",
            "address_line1",
            "address_line2",
            "city",
            "state",
            "zip_code",
            "license_number",
            "certifications",
            "primary_hospital",
        ]

    def validate(self, attrs):        
        if not attrs.get('speciality'):
            raise serializers.ValidationError(
                {'speciality': 'Speciality is required.'}
            )
        
        fees = attrs.get('fees')
        if fees is not None and fees <= 0:
            raise serializers.ValidationError(
                {'fees': 'Fees must be greater than zero.'}
            )

        lic = attrs.get('license_number')
        if lic and not re.match(r'^[A-Z0-9]{6,20}$', lic):
            raise serializers.ValidationError(
                {'license_number': '6-20 alphanumeric characters required.'}
            )
        
        user_to_onboard = attrs.get('user')
        if self.instance is None:
            if hasattr(user_to_onboard, "provider"):
                raise serializers.ValidationError(
                    {"user": "Provider profile already exists."}
                )

        return attrs

    def create(self, validated_data):
        user = validated_data.pop('user')
        return HealthcareProvider.objects.create(
            user=user,
            **validated_data
        )

    def update(self, instance, validated_data):
        validated_data.pop('user', None) # prevent user update
        # in case provider row already exists
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        return instance
