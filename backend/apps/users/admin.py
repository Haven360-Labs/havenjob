from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, TrustedSender, UserProviderSettings


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "full_name", "auth_provider", "subscription_tier", "onboarding_completed", "is_staff", "created_at")
    list_filter = ("auth_provider", "subscription_tier", "onboarding_completed", "is_staff", "is_active")
    search_fields = ("email", "full_name", "forwarding_address")
    ordering = ("-created_at",)
    readonly_fields = ("id", "created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("full_name", "forwarding_address", "target_role", "skills", "avatar_url")}),
        ("Onboarding", {"fields": ("onboarding_completed", "profile_completion_percent")}),
        ("Auth", {"fields": ("auth_provider",)}),
        ("Subscription (cloud)", {"fields": ("subscription_tier", "credits_balance")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser")}),
        ("Timestamps", {"fields": ("id", "created_at", "updated_at", "deleted_at")}),
    )

    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "forwarding_address", "password1", "password2")}),
    )


@admin.register(TrustedSender)
class TrustedSenderAdmin(admin.ModelAdmin):
    list_display = ("sender_email", "user", "label", "created_at")
    list_filter = ("created_at",)
    search_fields = ("sender_email", "label", "user__email")
    raw_id_fields = ("user",)
    readonly_fields = ("id", "created_at")


@admin.register(UserProviderSettings)
class UserProviderSettingsAdmin(admin.ModelAdmin):
    list_display = ("user", "provider_type", "provider_name", "created_at", "updated_at")
    list_filter = ("provider_type", "provider_name")
    search_fields = ("user__email",)
    raw_id_fields = ("user",)
    readonly_fields = ("id", "created_at", "updated_at")
