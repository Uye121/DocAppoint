from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, permission_classes, api_view, authentication_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.authentication import SessionAuthentication
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from django.middleware.csrf import get_token
from datetime import datetime, timedelta
from typing import List

from .models import (
    User, Patient, HealthcareProvider, AdminStaff, SystemAdmin,
    Appointment, MedicalRecord, Message, Speciality, Hospital,
    PatientProfile, AdminStaffProfile, HealthcareProviderProfile
)
from .serializers import (
    UserSerializer, PatientSerializer, HealthcareProviderSerializer,
    AppointmentSerializer, MedicalRecordSerializer, MessageSerializer,
    SpecialitySerializer, HospitalSerializer
)

from .permissions import (
    IsPatient, IsHealthcareProvider, IsAdminStaff, IsSystemAdmin,
    IsOwnerOrReadOnly, IsAppointmentParticipant, IsMessageParticipant,
    IsMedicalRecordProviderOrPatient, 
)

@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([SessionAuthentication])
def register_user(request):
    """
    Register a new user account
    """
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        
        if user.type == User.UserType.PATIENT:
            PatientProfile.objects.create(user=user)
        elif user.type == User.UserType.HEALTHCARE_PROVIDER: # type: ignore
            HealthcareProviderProfile.objects.create(user=user)
        elif user.type == User.UserType.ADMIN_STAFF: # type: ignore
            AdminStaffProfile.objects.create(user=user)
    
        login(request, user) # type: ignore
        
        return Response({
            'user': serializer.data
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([SessionAuthentication])
def login_user(request):
    """
    Login user with session authentication
    """
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response(
            {'error': 'Username and password required'},
            status=status.HTTP_400_BAD_REQUEST
        )
        
    user = authenticate(username=username, password=password)
    
    if user is not None:
        if user.is_active:
            login(request, user)
            serializer = UserSerializer(user)
            return Response({
                'user': serializer.data,
            })
        else:
            return Response(
                {'error': 'Account is disabled'},
                status=status.HTTP_401_UNAUTHORIZED
            )
    else:
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )
        
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_user(request):
    """
    Logout user
    """
    logout(request)
    return Response({'message': 'Logged out successfully'})