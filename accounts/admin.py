from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Role & Team", {"fields": ("role", "manager")}),
    )
    list_display = ("username", "email", "role", "manager", "is_staff")
    list_filter = ("role",)
