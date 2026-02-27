"""Pydantic schemas for notifications API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NotificationOut(BaseModel):
    """Response schema for a notification."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: str
    title: str
    message: str | None
    is_read: bool
    related_entity_type: str | None
    related_entity_id: UUID | None
    created_at: datetime
