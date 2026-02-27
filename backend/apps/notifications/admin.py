from django.contrib import admin
from .models import Notification, UserNotificationPreferences


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "type", "is_read", "is_email_sent", "related_entity_type", "created_at")
    list_filter = ("type", "is_read", "is_email_sent", "related_entity_type")
    search_fields = ("title", "message", "user__email")
    raw_id_fields = ("user",)
    readonly_fields = ("id", "created_at")
    date_hierarchy = "created_at"


@admin.register(UserNotificationPreferences)
class UserNotificationPreferencesAdmin(admin.ModelAdmin):
    list_display = ("user", "email_notifications_enabled", "in_app_notifications_enabled", "updated_at")
    list_filter = ("email_notifications_enabled", "in_app_notifications_enabled")
    search_fields = ("user__email",)
    raw_id_fields = ("user",)
    readonly_fields = ("id", "created_at", "updated_at")
