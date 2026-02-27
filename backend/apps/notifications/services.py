"""Notification creation helpers (e.g. trigger when application is auto-created)."""

from uuid import UUID

from apps.notifications.models import Notification, RelatedEntityType


def notify_application_created(
    user_id,
    application_id: UUID,
    *,
    title: str = "New application logged",
    message: str | None = "An application was added from your forwarded email.",
) -> Notification:
    """
    Create an in-app notification when an application is auto-created (e.g. from email).
    Call this from the email parsing / auto-create flow (EML-04 / EML-06).
    """
    return Notification.objects.create(
        user_id=user_id,
        type="application_created",
        title=title,
        message=message,
        is_read=False,
        related_entity_type=RelatedEntityType.APPLICATION,
        related_entity_id=application_id,
    )
