"""Schemas for inbound email webhook."""

from pydantic import BaseModel


class InboundEmailPayload(BaseModel):
    """Payload from email provider for inbound webhook."""

    sender: str
    recipient: str
    subject: str = ""
    body: str = ""
