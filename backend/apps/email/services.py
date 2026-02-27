"""Email webhook services (sender verification, auto-create application)."""

from datetime import datetime
from typing import Any

from django.utils import timezone

from apps.notifications.services import notify_application_created
from apps.tracker.models import Application, ApplicationStatus
from apps.users.models import User


def verify_sender(recipient_email: str, sender_email: str) -> User | None:
    """
    Verify that the sender is trusted for the recipient (user's forwarding address).
    Returns the User if recipient is a forwarding_address and sender is in trusted_senders; else None.
    """
    try:
        user = User.objects.get(forwarding_address__iexact=recipient_email)
    except User.DoesNotExist:
        return None
    if not user.trusted_senders.filter(sender_email__iexact=sender_email).exists():
        return None
    return user


def create_application_from_extracted(user: User, extracted: dict[str, Any]):
    """
    Create an Application from extracted email data (EML-04).
    Requires company_name and job_title; date_applied defaults to now if missing.
    Triggers notify_application_created (EML-06). Returns the Application or None.
    """
    company_name = extracted.get("company_name")
    job_title = extracted.get("job_title")
    if not company_name or not job_title:
        return None
    date_str = extracted.get("date_applied")
    if date_str and isinstance(date_str, str):
        try:
            date_applied = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            if timezone.is_naive(date_applied):
                date_applied = timezone.make_aware(date_applied)
        except (ValueError, TypeError):
            date_applied = timezone.now()
    else:
        date_applied = timezone.now()
    app = Application.objects.create(
        user=user,
        company_name=company_name[:255],
        job_title=job_title[:255],
        date_applied=date_applied,
        status=ApplicationStatus.APPLIED,
        source="Email",
    )
    notify_application_created(user.id, app.id)
    return app
