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

from ..models import User
from ..serializers.auth import SignUpSerializer
from ..services.auth import send_verification_email

@method_decorator(ratelimit(key="ip", rate="5/h", method="POST"), name='post')
class SignUpView(generics.CreateAPIView):
    serializer_class = SignUpSerializer
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        user = serializer.save()
        send_verification_email(user)

@method_decorator(ratelimit(key="ip", rate="10/h", method="POST"), name='post')
class LoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        print(f'{email} | {password}')
        user = authenticate(username=email, password=password)
        if user is None:
            return Response(
                { "detail": "Invalid credentials" },
                status=status.HTTP_401_UNAUTHORIZED
            )
        if not user.is_active:
            return Response(
                { "detail": "E-mail not verified" },
                status=status.HTTP_403_FORBIDDEN
            )
        
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username
                },
            }
        )

class VerifyEmailView(generics.GenericAPIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        uidb64 = kwargs["uid"]
        token = kwargs["token"]
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"detail": "Bad link"}, status=status.HTTP_400_BAD_REQUEST)

        if default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            return Response({"detail": "E-mail verified"}, status=status.HTTP_200_OK)
        return Response({"detail": "Bad or expired token"}, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(ratelimit(key="ip", rate="3/h", method="POST"), name='post')
class ResendVerifyView(generics.GenericAPIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        email = request.data.get("email")
        user = User.objects.filter(email=email).first()
        if user and not user.is_active:
            send_verification_email(user)
        return Response(status=status.HTTP_204_NO_CONTENT)
