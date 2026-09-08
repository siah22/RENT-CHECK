from django.test import TestCase
from django.urls import reverse
from accounts.models import User


class UserModelRoleTests(TestCase):
    def test_create_superuser_sets_admin_role(self):
        admin = User.objects.create_superuser(
            username="adminuser",
            email="admin@rentcheck.tz",
            password="StrongPassword123!"
        )
        self.assertEqual(admin.role, User.Role.ADMIN)
        self.assertTrue(admin.is_admin_role)
        self.assertFalse(admin.is_tenant)
        self.assertFalse(admin.is_owner_agent)
        self.assertEqual(admin.get_role_display(), "Administrator")

    def test_save_promotes_staff_or_superuser_to_admin(self):
        user = User.objects.create_user(
            username="staffuser",
            password="Password123!",
            is_staff=True
        )
        self.assertEqual(user.role, User.Role.ADMIN)
        self.assertTrue(user.is_admin_role)
        self.assertFalse(user.is_tenant)
        self.assertEqual(user.get_role_display(), "Administrator")

    def test_tenant_user_role(self):
        tenant = User.objects.create_user(
            username="tenant1",
            password="Password123!",
            role=User.Role.TENANT
        )
        self.assertEqual(tenant.role, User.Role.TENANT)
        self.assertTrue(tenant.is_tenant)
        self.assertFalse(tenant.is_admin_role)
        self.assertEqual(tenant.get_role_display(), "Tenant")


class PasswordToggleAndAuthViewsTests(TestCase):
    def test_login_page_contains_password_toggle(self):
        response = self.client.get(reverse("accounts:login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "toggle-password-btn")
        self.assertContains(response, "bi-eye")
        self.assertContains(response, 'data-target="id_password"')

    def test_register_page_contains_password_toggle(self):
        response = self.client.get(reverse("accounts:register"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "toggle-password-btn")
        self.assertContains(response, "bi-eye")

    def test_admin_redirected_to_dashboard_on_home(self):
        admin = User.objects.create_superuser(
            username="boss",
            password="Password123!"
        )
        self.client.force_login(admin)
        response = self.client.get(reverse("core:home"))
        self.assertRedirects(response, reverse("core:dashboard"))

    def test_admin_can_preview_home_with_preview_param(self):
        admin = User.objects.create_superuser(
            username="boss2",
            password="Password123!"
        )
        self.client.force_login(admin)
        response = self.client.get(reverse("core:home") + "?preview=1")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Admin Preview")

