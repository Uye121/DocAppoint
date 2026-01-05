import logging
from rest_framework.views import APIView
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils.decorators import method_decorator
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django_ratelimit.exceptions import Ratelimited

from ..models import User
from ..serializers import ChangePasswordSerializer, UserSerializer
from ..services.auth import send_verification_email
from ..utils.tokens import check_verification_jwt

logger = logging.getLogger(__name__)

# @method_decorator(ratelimit(key="ip", rate="10/h", method="POST"), name='post')
class LoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {"detail": "Missing email or password."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # check if user exist
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = None
        
        # Try to authenticate the user
        authenticated_user = authenticate(username=email, password=password)
        
        if authenticated_user is None:
            # If authentication failed, check if it's because user is inactive
            if user is not None and user.check_password(password) and not user.is_active:
                return Response(
                    { "detail": "E-mail not verified" },
                    status=status.HTTP_403_FORBIDDEN
                )
            return Response(
                { "detail": "Invalid credentials" },
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        refresh = RefreshToken.for_user(authenticated_user)
        user_data = UserSerializer(authenticated_user).data

        # remove None / blank optional fields
        user_data = {k: v for k, v in user_data.items() if v not in (None, "", [])}
        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": user_data,
            }
        )

class VerifyEmailView(generics.GenericAPIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        token = request.query_params.get("token")
        if not token:
            return Response({"detail": "Token required"}, status=400)

        uid = check_verification_jwt(token)
        if not uid:
            return Response({"detail": "Bad or expired token"}, status=400)
        
        user = get_object_or_404(User, pk=uid)

        if user.is_active:
            return Response({"detail": "E-mail already verified"}, status=200)

        user.is_active = True
        user.save(update_fields=["is_active"])
        return Response({"detail": "E-mail verified"}, status=status.HTTP_200_OK)

# @method_decorator(ratelimit(key="ip", rate="3/h", method="POST"), name='post')
class ResendVerifyView(generics.GenericAPIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        email = request.data.get("email", "").strip().lower()

        if not email:
            return Response(
                {"detail": "email required"}, status=status.HTTP_400_BAD_REQUEST
            )
        
        user = get_object_or_404(User, email=email)
        if user.is_active:
            return Response(
                {"detail": "account already verified"}, status=status.HTTP_400_BAD_REQUEST
            )
        
        user.reset_sent_at = timezone.now()
        user.save(update_fields=["reset_sent_at"])
        send_verification_email(user)

        return Response(status=status.HTTP_204_NO_CONTENT)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if user.check_password(serializer.validated_data['old_password']):
                user.set_password(serializer.validated_data['new_password'])
                user.save()
                return Response({"detail": "Password changed successfully."})
            return Response({"detail": "Old password is incorrect."},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class UserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


