import uuid
from django.db import models
from django.conf import settings


class RelatedEntityType(models.TextChoices):
    APPLICATION = "application", "Application"
    SYSTEM = "system", "System"
    BILLING = "billing", "Billing"


class Notification(models.Model):
    """User notification (in-app and optional email)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    type = models.CharField(max_length=50)  # Notification type; use TextChoices when set is fixed
    title = models.CharField(max_length=255)
    message = models.TextField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    is_email_sent = models.BooleanField(default=False)
    related_entity_type = models.CharField(
        max_length=20,
        choices=RelatedEntityType.choices,
        blank=True,
        null=True,
    )
    related_entity_id = models.UUIDField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.user_id})"


class UserNotificationPreferences(models.Model):
    """Per-user notification toggles."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
    )
    email_notifications_enabled = models.BooleanField(default=True)
    in_app_notifications_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_notification_preferences"

    def __str__(self):
        return f"Preferences for {self.user_id}"
