from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from ..models import MedicalRecord
from ..serializers import (
    MedicalRecordCreateSerializer,
    MedicalRecordUpdateSerializer,
    MedicalRecordListSerializer,
    MedicalRecordDetailSerializer
)
from ..permissions import (
    IsHealthcareProvider,
    IsPatientOrProvider,
    IsRecordOwner
)


class MedicalRecordViewSet(viewsets.ModelViewSet):
    """
    ViewSet for MedicalRecord with soft-delete support and role-based permissions.
    
    Endpoints:
    - GET /api/medical-record/ - List records (filtered by role)
    - POST /api/medical-record/ - Create new record (provider only)
    - GET /api/medical-record/{id}/ - Retrieve single record
    - PUT /api/medical-record/{id}/ - Update record (provider owner only)
    - PATCH /api/medical-record/{id}/ - Partial update (provider owner only)
    - DELETE /api/medical-record/{id}/ - Soft delete (provider owner only)
    """
    
    queryset = MedicalRecord.objects.filter(is_removed=False)
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['patient', 'healthcare_provider', 'hospital', 'appointment']
    search_fields = ['diagnosis', 'notes', 'prescriptions']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return MedicalRecordCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return MedicalRecordUpdateSerializer
        elif self.action == 'retrieve' or (self.action == 'list' and self.request.query_params.get('appointment')):
            return MedicalRecordDetailSerializer
        elif self.action == 'list':
            return MedicalRecordListSerializer
        # Default fallback
        return MedicalRecordDetailSerializer

    def get_permissions(self):
        """Instantiate and return the list of permissions for this view."""
        if self.action == 'create':
            permission_classes = [IsAuthenticated, IsHealthcareProvider]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsRecordOwner]
        elif self.action == 'list':
            permission_classes = [IsAuthenticated, IsPatientOrProvider]
        else:  # retrieve
            permission_classes = [IsAuthenticated, IsPatientOrProvider]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Filter queryset based on user role"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Patients can only see their own records
        if hasattr(user, 'patient'):
            queryset = queryset.filter(patient=user.patient)
        
        # Providers can only see records they created
        elif hasattr(user, 'provider'):
            queryset = queryset.filter(healthcare_provider=user.provider)
        
        # Admins/staff see all records
        elif user.is_staff:
            pass  # Return all records
        
        else:
            # Other users see nothing
            queryset = queryset.none()
        
        return queryset.select_related(
            'patient__user',
            'healthcare_provider__user',
            'healthcare_provider__speciality',
            'hospital',
            'created_by',
            'updated_by'
        )

    def perform_destroy(self, instance):
        """Soft delete instead of hard delete"""
        instance.is_removed = True
        instance.removed_at = timezone.now()
        instance.updated_by = self.request.user
        instance.save()

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def mine(self, request):
        """
        Get medical records for current user based on role.
        - Providers: records they created
        - Patients: their own records
        """
        queryset = self.get_queryset()
        
        # Apply additional filtering if needed
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def removed(self, request):
        """List soft-deleted records (admin/staff only)"""
        if not request.user.is_staff:
            return Response(
                {"detail": "You do not have permission to view deleted records."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        removed_records = MedicalRecord.objects.filter(is_removed=True)
        page = self.paginate_queryset(removed_records)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(removed_records, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def restore(self, request, pk=None):
        """Restore a soft-deleted record (admin/staff only)"""
        if not request.user.is_staff:
            return Response(
                {"detail": "You do not have permission to restore records."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        record = self.get_object()
        if not record.is_removed:
            return Response(
                {"detail": "Record is not deleted."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        record.is_removed = False
        record.removed_at = None
        record.updated_by = request.user
        record.save()
        
        return Response(
            {"detail": "Record restored successfully."},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def stats(self, request):
        """Get statistics about medical records"""
        user = request.user
        
        if hasattr(user, 'provider'):
            # Provider stats
            total_records = MedicalRecord.objects.filter(
                healthcare_provider=user.provider,
                is_removed=False
            ).count()
            
            recent_records = MedicalRecord.objects.filter(
                healthcare_provider=user.provider,
                created_at__gte=timezone.now() - timezone.timedelta(days=30),
                is_removed=False
            ).count()
            
            return Response({
                'total_records': total_records,
                'recent_records': recent_records,
                'role': 'provider'
            })
        
        elif hasattr(user, 'patient'):
            # Patient stats
            total_records = MedicalRecord.objects.filter(
                patient=user.patient,
                is_removed=False
            ).count()
            
            return Response({
                'total_records': total_records,
                'role': 'patient'
            })
        
        return Response({
            'role': 'other',
            'total_records': 0
        })
