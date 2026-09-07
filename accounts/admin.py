from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class RentCheckUserAdmin(UserAdmin):
    list_display = ["username", "email", "role", "account_status", "is_staff", "date_joined"]
    list_filter = ["role", "account_status", "is_staff"]
    fieldsets = UserAdmin.fieldsets + (
        ("RentCheck profile", {"fields": ("role", "phone_number", "account_status")}),
    )
