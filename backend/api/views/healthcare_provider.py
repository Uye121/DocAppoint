from django.utils import timezone
from rest_framework import exceptions
from rest_framework import mixins, viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from ..models import HealthcareProvider, User
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

    def get_serializer_class(self):
        if self.action == "create":
            return HealthcareProviderCreateSerializer
        if self.action == "onboard":
            return HealthcareProviderOnBoardSerializer
        if self.action == "list":
            return HealthcareProviderListSerializer
        return HealthcareProviderSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy", "onboard"):
            return [IsStaffOrAdmin()]
        return [permissions.IsAuthenticated()]

    def get_object(self):
        
        if 'pk' in self.kwargs:
            # Staff or the provider themselves accessing via ID
            return HealthcareProvider.objects.get(user_id=self.kwargs['pk'])
        return self.request.user.provider
    
    @action(detail=False, methods=["get", "patch", "put"], url_path="me")
    def me(self, request):
        if not hasattr(request.user, 'provider'):
            raise exceptions.NotFound("Provider profile not found.")

        if request.method == "GET":
            serializer = self.get_serializer(request.user.provider)
            return Response(serializer.data)
        else:  # PATCH/PUT
            serializer = self.get_serializer(
                request.user.provider, 
                data=request.data, 
                partial=(request.method == "PATCH")
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="onboard")
    def onboard(self, request):        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"detail": "Provider profile created."}, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        return serializer.save()

    def perform_update(self, serializer):
        user = self.request.user
        instance = self.get_object()
        can_update = False

        if user.is_staff or hasattr(user, 'system_admin'):
            can_update = True
        elif hasattr(user, 'admin_staff'):
            print('prov: ', instance.primary_hospital.name)
            print('admin: ', user.admin_staff.hospital.name)
            if instance.primary_hospital and instance.primary_hospital == user.admin_staff.hospital:
                can_update = True

        if can_update and serializer.validated_data.get("is_removed") is True:
            instance = serializer.save()
            instance.removed_at = timezone.now()
            instance.save(update_fields=["removed_at"])
        else:
            super().perform_update(serializer)