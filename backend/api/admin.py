from django.contrib import admin
from .models import CustomUser, Speciality, Doctor, Role

admin.site.register(CustomUser)
admin.site.register(Speciality)
admin.site.register(Doctor)
admin.site.register(Role) 