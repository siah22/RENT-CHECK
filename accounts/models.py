from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        TENANT = "TENANT", "Tenant"
        OWNER_AGENT = "OWNER_AGENT", "Owner / Agent"
        ADMIN = "ADMIN", "Administrator"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        SUSPENDED = "SUSPENDED", "Suspended"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.TENANT)
    phone_number = models.CharField(max_length=20, blank=True)
    account_status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_tenant(self):
        return self.role == self.Role.TENANT

    @property
    def is_owner_agent(self):
        return self.role == self.Role.OWNER_AGENT

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
