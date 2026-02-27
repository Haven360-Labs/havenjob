"""Pydantic schemas for users API."""

from pydantic import BaseModel, Field


class RegistrationIn(BaseModel):
    """Payload for email/password registration. forwarding_address optional; generated if omitted (ONB-01)."""

    email: str = Field(..., max_length=254)
    forwarding_address: str | None = Field(None, max_length=254)
    password: str = Field(..., min_length=8)
    full_name: str | None = Field(None, max_length=255)


class RegistrationOut(BaseModel):
    """Response after successful registration."""

    id: str
    email: str
    forwarding_address: str


class LoginIn(BaseModel):
    """Payload for login."""

    email: str = Field(..., max_length=254)
    password: str = Field(...)


class UserMeOut(BaseModel):
    """Current user (for /me and login response)."""

    id: str
    email: str
    forwarding_address: str | None = None
    full_name: str | None = None
    target_role: str | None = None
    onboarding_completed: bool = False


class UserMePatchIn(BaseModel):
    """Optional fields for PATCH /me (onboarding, profile)."""

    full_name: str | None = Field(None, max_length=255)
    target_role: str | None = Field(None, max_length=255)
    onboarding_completed: bool | None = None


class TrustedSenderOut(BaseModel):
    """Trusted sender for email parsing."""

    id: str
    sender_email: str
    label: str | None = None


class TrustedSenderIn(BaseModel):
    """Payload to add a trusted sender."""

    sender_email: str = Field(..., max_length=254)
    label: str | None = Field(None, max_length=255)
