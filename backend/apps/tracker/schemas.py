"""Pydantic schemas for tracker API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


APPLICATION_STATUS_VALUES = [
    "Applied",
    "Under Review",
    "Phone Screen",
    "Interview",
    "Offer",
    "Accepted",
    "Rejected",
    "Withdrawn",
]


class ApplicationIn(BaseModel):
    """Payload for creating a job application."""

    company_name: str = Field(..., max_length=255, description="Company name")
    job_title: str = Field(..., max_length=255, description="Job title")
    date_applied: datetime = Field(..., description="When the application was submitted")
    status: str = Field(..., description="Application status")
    source: str | None = Field(None, max_length=255)
    notes: str | None = None
    deadline: datetime | None = None
    follow_up_date: datetime | None = None
    job_url: HttpUrl | str | None = None
    location: str | None = Field(None, max_length=255)
    salary_min: int | None = None
    salary_max: int | None = None
    salary_currency: str | None = Field(None, max_length=3)

    @field_validator("status")
    @classmethod
    def status_one_of(cls, v: str) -> str:
        if v not in APPLICATION_STATUS_VALUES:
            msg = f"status must be one of {APPLICATION_STATUS_VALUES}"
            raise ValueError(msg)
        return v


class ApplicationStatusUpdateIn(BaseModel):
    """Payload for updating an application's status."""

    status: str = Field(..., description="New application status")

    @field_validator("status")
    @classmethod
    def status_one_of(cls, v: str) -> str:
        if v not in APPLICATION_STATUS_VALUES:
            msg = f"status must be one of {APPLICATION_STATUS_VALUES}"
            raise ValueError(msg)
        return v


class ApplicationOut(BaseModel):
    """Response schema for a job application."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_name: str
    job_title: str
    date_applied: datetime
    status: str
    source: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
