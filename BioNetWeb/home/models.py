from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, name, organization, password, **extra_fields):
        if not all([email, name, organization, password]):
            raise ValueError("All fields are required")
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, organization=organization, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, name, organization, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        return self._create_user(email=email, name=name, organization=organization, password=password, **extra_fields)

    def create_superuser(self, email, name, organization, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        #extra_fields.setdefault("is_admin", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')

        return self._create_user(email, name, organization, password, **extra_fields)

class MyUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_('email address'), unique=True)
    name = models.CharField(max_length=40)
    organization = models.CharField(max_length=100)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    can_use_monsoon = models.BooleanField(default=False)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'organization']
    #REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        
