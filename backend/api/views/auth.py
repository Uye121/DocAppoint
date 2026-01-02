import logging
from rest_framework.views import APIView
from django_ratelimit.decorators import ratelimit
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.utils.decorators import method_decorator
from rest_framework.permissions import IsAuthenticated
from django_ratelimit.exceptions import Ratelimited

from ..models import User
from ..serializers import ChangePasswordSerializer, UserSerializer
from ..services.auth import send_verification_email

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
        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": {
                    "id": authenticated_user.id,
                    "email": authenticated_user.email,
                    "username": authenticated_user.username
                },
            }
        )

class VerifyEmailView(generics.GenericAPIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        key = kwargs["key"]

        try:
            uidb64, token = key.split("-", 1)
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"detail": "Bad link"}, status=status.HTTP_400_BAD_REQUEST)

        if default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            return Response({"detail": "E-mail verified"}, status=status.HTTP_200_OK)
        return Response({"detail": "Bad or expired token"}, status=status.HTTP_400_BAD_REQUEST)

# @method_decorator(ratelimit(key="ip", rate="3/h", method="POST"), name='post')
class ResendVerifyView(generics.GenericAPIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        try:
            uid64 = request.data.get("uid")
            uid = force_str(urlsafe_base64_decode(uid64))
            user = User.objects.get(pk=uid)
        except Exception:
            return Response({"detail": "Invalid uid"}, status=status.HTTP_400_BAD_REQUEST)

        if user and not user.is_active:
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


