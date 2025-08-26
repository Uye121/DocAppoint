from django.shortcuts import render
from django.contrib.auth.models import AnonymousUser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from .models import Speciality, Doctor
from .serializers import SpecialitySerializer, DoctorSerializer
from .permissions import AdminOnlyEdit

class SpecialityListCreateView(generics.ListCreateAPIView):
    queryset = Speciality.objects.all()
    serializer_class = SpecialitySerializer
    permission_classes = [AdminOnlyEdit] 
    
    def perform_create(self, serializer):
        serializer.save()
        
class DoctorListCreateView(generics.ListCreateAPIView):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [AdminOnlyEdit] 
    
    def perform_create(self, serializer):
        serializer.save()
        
class DoctorDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, pk):
        try:
            doctor = Doctor.objects.get(pk=pk)
            doctor.delete()
            return Response(
                {"message": "Doctor deleted successfully."},
                status=status.HTTP_204_NO_CONTENT
            )
        except Doctor.DoesNotExist:
            return Response(
                {"error": "Doctor not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
class DoctorBySpecialityView(generics.ListAPIView):
    serializer_class = DoctorSerializer
    
    def get_queryset(self):
        speciality = self.kwargs['speciality']
        return Doctor.objects.filter(speciality__name=speciality)
