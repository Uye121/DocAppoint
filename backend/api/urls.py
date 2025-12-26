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
from rest_framework_simplejwt.views import TokenRefreshView

from .views.auth import (
    SignUpView,
    LoginView,
    VerifyEmailView,
    ResendVerifyView,
    LogoutView,
    ChangePasswordView,
    UserView,
)
from .views.healthcare_provider import (
    HealthcareProviderListView,
    HealthcareProviderProfileView,
    MyHealthcareProviderProfileView,
    HealthcareProviderStatisticsView
)
from .views.speciality import (
    SpecialityListView,
    SpecialityDetailView,
    SpecialityCreateView,
    SpecialityUpdateView,
    SpecialityDeleteView
)

authpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("verify/<str:key>/", VerifyEmailView.as_view(), name="verify_email"),
    path("resend-verify/", ResendVerifyView.as_view(), name="resend_verify"),
    path("password-reset/", include("django_rest_passwordreset.urls")), # TODO: to be modified
    path("logout/", LogoutView.as_view(), name="logout"),
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),
    path("me/", UserView.as_view(), name="user_info")
]

providerpatterns = [
    path("", HealthcareProviderListView.as_view(), name="provider_list"),
    path("<uuid:id>/", HealthcareProviderProfileView.as_view(), name="provider_detail"),
    path("me/", MyHealthcareProviderProfileView.as_view(), name="my_provider_profile"),
    path("statistics/", HealthcareProviderStatisticsView.as_view(), name="provider_dashboard"),
]

specialitypatterns = [
    path("", SpecialityListView.as_view(), name="speciality_list"),
    path("<int:id>/", SpecialityDetailView.as_view(), name="speciality_detail"),
    path("create/", SpecialityCreateView.as_view(), name="speciality_create"),
    path("<int:id>/update/", SpecialityUpdateView.as_view(), name="speciality_update"),
    path("<int:id>/delete/", SpecialityDeleteView.as_view(), name="speciality_delete"),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/", include(authpatterns)),
    path("api/providers/", include(providerpatterns)),
    path("api/specialities/", include(specialitypatterns)),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
