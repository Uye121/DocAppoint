from rest_framework import mixins, viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from ..models import Patient
from ..serializers import (
    PatientSerializer,
    PatientCreateSerializer,
    PatientOnBoardSerializer,
)


class PatientViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    Features:
        - Anyone can sign-up as patient (create)
        - Authenticated users can turn themselves into a patient (onboard)
        - Each patient can read / update their own profile
        - Staff can list all patients
    """

    queryset = Patient.objects.select_related("user")
    pagination_class = PageNumberPagination

    def get_serializer_class(self):
        if self.action == "create":
            return PatientCreateSerializer
        if self.action == "on_board":
            return PatientOnBoardSerializer
        return PatientSerializer

    def get_permissions(self):
        if self.action in ("create", "list"):
            return (
                [permissions.AllowAny()]
                if self.action == "create"
                else [permissions.IsAuthenticated()]
            )
        return [permissions.IsAuthenticated()]

    def get_object(self):
        return self.request.user.patient

    def perform_create(self, serializer):
        return serializer.save()

    def update(self, request, *args, **kwargs):
        """Only allow patients to update their own profile"""
        instance = self.get_object()
        if instance.user != request.user and not request.user.is_staff:
            return Response(
                {"detail": "You can only update your own patient profile."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().update(request, *args, **kwargs)

    @action(detail=False, methods=["post"], url_path="onboard")
    def on_board(self, request):
        if hasattr(request.user, "patient"):
            return Response(
                {"detail": "Patient profile already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Patient profile created."}, status=status.HTTP_201_CREATED
        )

    def list(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return super().list(request, *args, **kwargs)
