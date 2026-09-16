from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUserManager(DjangoUserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "ADMIN")
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        TENANT = "TENANT", _("Tenant")
        OWNER_AGENT = "OWNER_AGENT", _("Owner / Agent")
        ADMIN = "ADMIN", _("Administrator")

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", _("Active")
        SUSPENDED = "SUSPENDED", _("Suspended")

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.TENANT)
    phone_number = models.CharField(max_length=20, blank=True)
    account_status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        # Automatically assign ADMIN role to superusers or staff members if still marked as default
        if (self.is_superuser or self.is_staff) and self.role == self.Role.TENANT:
            self.role = self.Role.ADMIN
        super().save(*args, **kwargs)

    @property
    def is_tenant(self):
        return self.role == self.Role.TENANT and not self.is_admin_role

    @property
    def is_owner_agent(self):
        return self.role == self.Role.OWNER_AGENT and not self.is_admin_role

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN or self.is_superuser or self.is_staff

    def get_role_display(self):
        if self.is_admin_role:
            return _("Administrator")
        try:
            return self.Role(self.role).label
        except (ValueError, KeyError):
            return self.role

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
