"""Email webhook API (inbound from email provider)."""

from ninja import Router

from apps.email.extraction import extract_job_info
from apps.email.schemas import InboundEmailPayload
from apps.email.services import create_application_from_extracted, verify_sender

router = Router(tags=["email"])


@router.post("webhook", response={200: dict})
def inbound_webhook(request, payload: InboundEmailPayload):
    """
    Receive incoming parsed emails from the email provider.
    Verifies sender against recipient user's trusted_senders; drops if unverified.
    When verified and subject/body present, extracts company, job title, date (EML-03).
    """
    user = verify_sender(
        recipient_email=payload.recipient,
        sender_email=payload.sender,
    )
    out = {"received": True, "verified": user is not None}
    if user is not None and (payload.subject or payload.body):
        out["extracted"] = extract_job_info(
            subject=payload.subject or "",
            body=payload.body or "",
        )
        app = create_application_from_extracted(user, out["extracted"])
        if app is not None:
            out["application_id"] = str(app.id)
    return 200, out
