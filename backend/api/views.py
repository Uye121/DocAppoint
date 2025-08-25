from django.shortcuts import render
from django.contrib.auth.models import AnonymousUser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, filters
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from .models import Speciality, Doctor
from .serializers import SpecialitySerializer, DoctorSerializer
from .permissions import AdminOnlyEdit

class SpecialityListCreateView(generics.ListCreateAPIView):
    queryset = Speciality.objects.all()
    serializer_class = SpecialitySerializer
    # permission_classes = [AdminOnlyEdit] 
    
    def perform_create(self, serializer):
        """
        Save Speciality instance with admin-only permission to edit.

        Args:
            serializer (SpecialitySerializer): Serializer instance containing
            Speciality data.

        Raises:
            PermissionDenied: If request comes from non-admin user
        """
        if self.request.user.is_anonymous or not self.request.user.is_admin:
            raise PermissionDenied("Only admins can edit Speciality.")
        serializer.save()
        
class DoctorListCreateView(generics.ListCreateAPIView):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    # permission_classes = [AdminOnlyEdit] 
    
    def perform_create(self, serializer):
        """
        Save Doctor instance with admin-only permission to edit.

        Args:
            serializer (DoctorSerializer): Serializer instance containing
            Doctor data.

        Raises:
            PermissionDenied: If request comes from non-admin user
        """
        # if self.request.user.is_anonymous or not self.request.user.is_admin:
        #     raise PermissionDenied("Only admins can edit Doctor.")
        serializer.save()
        
class DoctorBySpecialityView(generics.ListAPIView):
    serializer_class = DoctorSerializer
    # permission_classes = [AdminOnlyEdit] 
    
    def get_queryset(self):
        speciality = self.kwargs['speciality']
        return Doctor.objects.filter(speciality=speciality)
