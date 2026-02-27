from ninja import Router

from apps.notifications.models import Notification
from apps.notifications.schemas import NotificationOut

router = Router(tags=["notifications"])


@router.get("", response={200: list[NotificationOut], 401: dict})
def list_notifications(request):
    """List the current user's notifications (newest first). Requires authentication."""
    if not request.user.is_authenticated:
        return 401, {"detail": "Authentication required"}
    qs = Notification.objects.filter(user=request.user).order_by("-created_at")[:50]
    return 200, list(qs)


@router.patch("{notification_id}", response={200: NotificationOut, 401: dict, 403: dict, 404: dict})
def mark_notification_read(request, notification_id):
    """Mark a notification as read. Requires authentication; must own the notification."""
    if not request.user.is_authenticated:
        return 401, {"detail": "Authentication required"}
    try:
        notification = Notification.objects.get(pk=notification_id)
    except Notification.DoesNotExist:
        return 404, {"detail": "Notification not found"}
    if notification.user_id != request.user.id:
        return 403, {"detail": "Forbidden"}
    notification.is_read = True
    notification.save(update_fields=["is_read"])
    return 200, notification
