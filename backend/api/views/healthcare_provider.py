from django.utils import timezone
from rest_framework import exceptions
from rest_framework import mixins, viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from ..models import HealthcareProvider, Hospital, ProviderHospitalAssignment
from ..serializers import (
    HealthcareProviderSerializer,
    HealthcareProviderCreateSerializer,
    HealthcareProviderOnBoardSerializer,
    HealthcareProviderListSerializer,
)
from ..permissions import IsStaffOrAdmin


class HealthcareProviderViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    Features
        - Public list (active, non-deleted) with search / filter
        - Authenticated provider can onboard themselves
        - Each provider owns their own profile (R/U)
        - Staff full CRUD
    """

    queryset = HealthcareProvider.objects.filter(
        is_removed=False, user__is_active=True
    ).select_related("user", "speciality", "primary_hospital")
    pagination_class = PageNumberPagination
    filterset_fields = ["speciality"]
    search_fields = ["user__first_name", "user__last_name", "speciality__name"]

    def get_serializer_class(self):
        if self.action == "create":
            return HealthcareProviderCreateSerializer
        if self.action == "onboard":
            return HealthcareProviderOnBoardSerializer
        if self.action == "list":
            return HealthcareProviderListSerializer
        return HealthcareProviderSerializer

    def get_permissions(self):
        staff_actions = [
            "create", "update", "partial_update", "destroy", "onboard",
            "assign_hospital", "unassign_hospital", "hospitals"
        ]

        if self.action in staff_actions:
            return [IsStaffOrAdmin()]
        return [permissions.IsAuthenticated()]

    def get_object(self):
        if "pk" in self.kwargs:
            # Staff or the provider themselves accessing via ID
            return HealthcareProvider.objects.get(user_id=self.kwargs["pk"])
        return self.request.user.provider

    @action(detail=False, methods=["get", "patch", "put"], url_path="me")
    def me(self, request):
        if not hasattr(request.user, "provider"):
            raise exceptions.NotFound("Provider profile not found.")

        if request.method == "GET":
            serializer = self.get_serializer(request.user.provider)
            return Response(serializer.data)
        else:  # PATCH/PUT
            serializer = self.get_serializer(
                request.user.provider,
                data=request.data,
                partial=(request.method == "PATCH"),
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="onboard")
    def onboard(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"detail": "Provider profile created."}, status=status.HTTP_201_CREATED
        )

    def perform_create(self, serializer):
        return serializer.save()

    def perform_update(self, serializer):
        user = self.request.user
        instance = self.get_object()
        can_update = False

        if user.is_staff or hasattr(user, "system_admin"):
            can_update = True
        elif hasattr(user, "admin_staff"):
            if (
                instance.primary_hospital
                and instance.primary_hospital == user.admin_staff.hospital
            ):
                can_update = True

        if can_update and serializer.validated_data.get("is_removed") is True:
            instance = serializer.save()
            instance.removed_at = timezone.now()
            instance.save(update_fields=["removed_at"])
        else:
            super().perform_update(serializer)

    @action(detail=True, methods=['post'], permission_classes=[IsStaffOrAdmin])
    def assign_hospital(self, request, pk=None):
        provider = self.get_object()
        hospital_id = request.data.get('hospital_id')
        
        try:
            hospital = Hospital.objects.get(id=hospital_id)
        except Hospital.DoesNotExist:
            return Response(
                {"error": "Hospital not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if assignment already exists
        assignment, created = ProviderHospitalAssignment.objects.get_or_create(
            healthcare_provider=provider,
            hospital=hospital,
            defaults={
                'is_active': True,
                'created_by': request.user,
                'updated_by': request.user,
            }
        )
        
        if not created and not assignment.is_active:
            assignment.is_active = True
            assignment.save(update_fields=['is_active', 'updated_by'])
            return Response({"message": "Assignment reactivated"}, status=status.HTTP_200_OK)
        elif not created:
            return Response(
                {"error": "Assignment already exists"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(
            {"message": "Hospital assigned successfully"}, 
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsStaffOrAdmin])
    def unassign_hospital(self, request, pk=None):
        provider = self.get_object()
        hospital_id = request.data.get('hospital_id')
        
        try:
            assignment = ProviderHospitalAssignment.objects.get(
                healthcare_provider=provider,
                hospital_id=hospital_id,
                is_active=True
            )
        except ProviderHospitalAssignment.DoesNotExist:
            return Response(
                {"error": "Active assignment not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        assignment.is_active = False
        assignment.updated_by = request.user
        assignment.save(update_fields=['is_active', 'updated_by'])
        
        return Response(
            {"message": "Hospital unassigned successfully"}, 
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['get'], permission_classes=[IsStaffOrAdmin])
    def hospitals(self, request, pk=None):
        provider = self.get_object()
        assignments = provider.providerhospitalassignment_set.filter(is_active=True)
        
        primary_hospital_id = provider.primary_hospital.id if provider.primary_hospital else None

        hospitals = [
            {
                'id': assignment.hospital.id,
                'name': assignment.hospital.name,
                'start_datetime_utc': assignment.start_datetime_utc,
                'is_primary': primary_hospital_id == assignment.hospital.id
            }
            for assignment in assignments
        ]
        
        return Response(hospitals)
