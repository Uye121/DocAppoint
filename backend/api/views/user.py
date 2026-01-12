from django.contrib.auth import get_user_model
from rest_framework import status, mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import User
from ..serializers import (
    UserSerializer,
    ChangePasswordSerializer,
)
from ..services.auth import send_verification_email

User = get_user_model()

class UserViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    Features:
        - Public sign-up
        - Authenticated profile read / update
        - Authenticated password change
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self):
        return self.request.user
    
    def perform_create(self, serializer):
        user = serializer.save()
        send_verification_email(user)

    @action(detail=False, methods=["post"], url_path="change-password")
    def change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not user.check_password(serializer.validated_data["old_password"]):
            return Response(
                {"old_password": "Wrong password."}, status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save()
        return Response({"detail": "Password updated."}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=["get", "put", "patch"], url_path="me")
    def me(self, request):        
        user = request.user
        
        if request.method == "GET":
            serializer = self.get_serializer(user)
            return Response(serializer.data)
        
        elif request.method in ["PUT", "PATCH"]:
            partial = request.method == "PATCH"
            serializer = self.get_serializer(user, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)