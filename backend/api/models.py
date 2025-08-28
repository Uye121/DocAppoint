from django.db import models
from django.utils import timezone
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin

class BaseModel(models.Model):
    created_at = models.DateTimeField(db_index=True, default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
        
class RoleName:
    PATIENT = "Patient"
    HEALTHCARE_PROVIDER = "Healthcare Provider"
    ADMINISTRATIVE_STAFF = "Administrative Staff"
    SYSTEM_ADMIN = "System Admin"
        
class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name
    
    @classmethod
    def create_core_roles(cls):
        core_roles = [
            (RoleName.PATIENT, "A patient user who can schedule appointments with healthcare providers."),
            (RoleName.HEALTHCARE_PROVIDER, "A doctor or specialist who can consult with patients."),
            (RoleName.ADMINISTRATIVE_STAFF, "Staff who manages the appointment schedules but have limited interaction and access to patient data."),
            (RoleName.SYSTEM_ADMIN, "Technical admin with full system access, but not clinical data access.")
        ]
        for name, desc in core_roles:
            cls.objects.get_or_create(name=name, defaults={'description': desc})

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password, first_name, last_name, date_of_birth):
        """
        Creates and saves a regular user with given email, password, and name

        Args:
            email (string): user's email
            password (string): user's password
            first_name (string): user's first name
            last_name (string): user's last name
            date_of_birth (date): user's date of birth
        """
        if not email:
            raise ValueError("Users must have an email address")
        if not password:
            raise ValueError("Users must include password")
        if not first_name:
            raise ValueError("User must have a first name")
        if not last_name:
            raise ValueError("User must have a last name")
        if not date_of_birth:
            raise ValueError("User must provide a date of birth")
        
        user = self.model(
            email=self.normalize_email(email),
            date_of_birth=date_of_birth,
            first_name=first_name,
            last_name=last_name
        )
        
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password, first_name, last_name, date_of_birth=None):
        """
        Creates and saves a super user with given email, password, and name

        Args:
            email (string): user's email
            password (string): user's password
            first_name (string): user's first name
            last_name (string): user's last name
            date_of_birth (date): user's date of birth
        """
        user = self.create_user(
            email,
            password,
            first_name,
            last_name,
            date_of_birth,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user

class CustomUser(AbstractBaseUser, BaseModel, PermissionsMixin):
    email = models.EmailField(max_length=255, unique=True)
    date_of_birth = models.DateField()
    first_name = models.CharField(max_length=1024)
    last_name = models.CharField(max_length=1024)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    
    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["date_of_birth", "first_name", "last_name"]
    
    def __str__(self):
        return self.email
    
    @property
    def is_staff(self):
        return self.is_admin
    
class Speciality(models.Model):
    name = models.CharField(max_length=180, unique=True)
    image = models.FileField(upload_to='speciality')
    
    def __str__(self):
        return self.name
    
class Doctor(models.Model):
    speciality = models.ForeignKey(Speciality, on_delete=models.CASCADE, related_name='doctors')
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    image = models.ImageField(upload_to='doctors')
    degree = models.CharField(max_length=100)
    experience = models.DecimalField(max_digits=4, decimal_places=2)
    about = models.TextField()
    fees = models.DecimalField(max_digits=9, decimal_places=2)
    address_line1 = models.CharField("Address line 1", max_length=1024)
    address_line2 = models.CharField("Address line 2", max_length=1024, blank=True)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=2)
    zip_code = models.CharField(max_length=5)
    
    class Meta:
        constraints = [
            models.CheckConstraint(
                name="experience_non_negative",
                check=models.Q(experience__gte=0)
            ),
            models.CheckConstraint(
                name="fees_above_0",
                check=models.Q(fees__gt=0)
            )
        ]
