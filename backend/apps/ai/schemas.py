"""Pydantic schemas for AI app API."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CVDocumentOut(BaseModel):
    """Response schema for an uploaded CV document."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    file_name: str
    file_url: str
    is_primary: bool
    uploaded_at: datetime


class ChatSessionOut(BaseModel):
    """Response schema for a chat session."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str | None
    created_at: datetime
    updated_at: datetime


class ChatMessageOut(BaseModel):
    """Response schema for a chat message."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: str
    content: str
    created_at: datetime


class ChatMessageIn(BaseModel):
    """Payload for sending a chat message."""

    content: str


class ImproveAnswerIn(BaseModel):
    """Payload for improving a draft interview answer."""

    draft_answer: str
    question: str | None = None
    user_answer_id: UUID | None = None


class CoverLetterIn(BaseModel):
    """Payload for cover letter generation."""

    job_description: str
    tone: str = "formal"


class CoverLetterOut(BaseModel):
    """Response with generated cover letter text."""

    cover_letter: str


class ImproveAnswerOut(BaseModel):
    """Response with LLM-improved STAR-formatted answer."""

    improved_answer: str


class InterviewQuestionOut(BaseModel):
    """Response schema for an interview question."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    category: str
    question_type: str
    question: str
    created_at: datetime


class UserAnswerOut(BaseModel):
    """Response schema for a user's answer."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    question_id: UUID | None
    custom_question: str | None
    draft_answer: str | None
    ai_improved_answer: str | None
    is_ai_generated: bool
    created_at: datetime
    updated_at: datetime


class UserAnswerIn(BaseModel):
    """Payload for creating/updating a user answer."""

    question_id: UUID | None = None
    custom_question: str | None = None
    draft_answer: str | None = None


# Profile: work experience and projects (AI-02)


class WorkExperienceIn(BaseModel):
    """Payload for creating/updating work experience."""

    company: str
    role: str
    start_date: date
    end_date: date | None = None
    is_current: bool = False
    description: str | None = None
    display_order: int = 0


class WorkExperienceOut(BaseModel):
    """Response schema for work experience."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company: str
    role: str
    start_date: date
    end_date: date | None
    is_current: bool
    description: str | None
    display_order: int
    created_at: datetime
    updated_at: datetime


class ProjectIn(BaseModel):
    """Payload for creating/updating a project."""

    title: str
    description: str
    technologies: list[str] | None = None
    url: str | None = None
    display_order: int = 0


class ProjectOut(BaseModel):
    """Response schema for a project."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str
    technologies: list | None
    url: str | None
    display_order: int
    created_at: datetime
    updated_at: datetime
