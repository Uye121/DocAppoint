"""
URL configuration for api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    UserViewSet,
    LoginView,
    VerifyEmailView,
    ResendVerifyView,
    LogoutView,
    ChangePasswordView,
    UserView,
    PatientViewSet,
    HealthcareProviderViewSet,
    SpecialityViewSet,
    AppointmentViewSet,
    SlotViewSet,
)

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")
router.register("patient", PatientViewSet, basename="patient")
router.register("provider", HealthcareProviderViewSet, basename="provider")
router.register("speciality", SpecialityViewSet, basename="speciality")
router.register("appointment", AppointmentViewSet, basename="appointment")
router.register("slot", SlotViewSet, basename="slot")
# router.register("patients", PatientViewSet, basename="patient")
# router.register("providers", HealthcareProviderViewSet, basename="provider")

authpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("verify/", VerifyEmailView.as_view(), name="verify_email"),
    path("resend-verify/", ResendVerifyView.as_view(), name="resend_verify"),
    path(
        "password-reset/", include("django_rest_passwordreset.urls")
    ),  # TODO: to be modified
    path("logout/", LogoutView.as_view(), name="logout"),
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),
    path("me/", UserView.as_view(), name="user_info"),
]


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include(authpatterns)),
    path("api/", include(router.urls)),
    # path("api/providers/", include(providerpatterns)),
    # path("api/specialities/", include(specialitypatterns)),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
