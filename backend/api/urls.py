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
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
# from .views import SpecialityListCreateView, DoctorListCreateView, DoctorBySpecialityView, DoctorDeleteView

urlpatterns = [
    # path('admin/', admin.site.urls),
    # path('specialities/', SpecialityListCreateView.as_view(), name='speciality-list-create'),
    # path('doctors/', DoctorListCreateView.as_view(), name='doctor-list-create'),
    # path('doctors/speciality/<str:speciality>', DoctorBySpecialityView.as_view(), name='doctors-by-speciality'),
    # path('doctors/<int:pk>/delete', DoctorDeleteView.as_view(), name='doctor-delete')
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
