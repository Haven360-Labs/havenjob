import uuid
from django.db import models
from django.conf import settings


class Education(models.Model):
    """User education entry for CV/assistant."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="education",
    )
    institution = models.CharField(max_length=255)
    degree = models.CharField(max_length=255)
    field_of_study = models.CharField(max_length=255, blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    is_current = models.BooleanField(default=False)
    grade = models.CharField(max_length=100, blank=True, null=True)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "education"
        ordering = ["display_order", "start_date"]

    def __str__(self):
        return f"{self.degree} at {self.institution}"


class WorkExperience(models.Model):
    """User work experience for CV/assistant."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="work_experiences",
    )
    company = models.CharField(max_length=255)
    role = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    is_current = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "work_experiences"
        ordering = ["display_order", "start_date"]

    def __str__(self):
        return f"{self.role} at {self.company}"


class Project(models.Model):
    """User project for CV/assistant."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="projects",
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    technologies = models.JSONField(default=list, blank=True, null=True)
    url = models.URLField(max_length=2000, blank=True, null=True)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "projects"
        ordering = ["display_order"]

    def __str__(self):
        return self.title


class CVDocument(models.Model):
    """Uploaded CV/resume with optional parsed text."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cv_documents",
    )
    file_name = models.CharField(max_length=255)
    file_url = models.CharField(max_length=2000)
    parsed_text = models.TextField(blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "cv_documents"
        ordering = ["-is_primary", "-uploaded_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                name="unique_user_primary_cv",
                condition=models.Q(is_primary=True),
            )
        ]

    def __str__(self):
        return self.file_name


class JobDescription(models.Model):
    """Stored job description text (for matching and AI)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="job_descriptions",
    )
    application = models.ForeignKey(
        "tracker.Application",
        on_delete=models.SET_NULL,
        related_name="job_descriptions",
        blank=True,
        null=True,
    )
    company_name = models.CharField(max_length=255, blank=True, null=True)
    job_title = models.CharField(max_length=255, blank=True, null=True)
    raw_text = models.TextField()
    content_hash = models.CharField(max_length=64, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "job_descriptions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["content_hash"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "content_hash"],
                name="unique_user_content_hash",
                condition=models.Q(content_hash__isnull=False),
            )
        ]

    def __str__(self):
        return self.job_title or str(self.id)


class QuestionType(models.TextChoices):
    BEHAVIOURAL = "behavioural", "Behavioural"
    STANDARD = "standard", "Standard"


class InterviewQuestion(models.Model):
    """Seed interview questions (not user-specific)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.CharField(max_length=255)
    question_type = models.CharField(
        max_length=20,
        choices=QuestionType.choices,
    )
    question = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "interview_questions"
        ordering = ["category", "created_at"]

    def __str__(self):
        return self.question[:80] + "..." if len(self.question) > 80 else self.question


class UserAnswer(models.Model):
    """User's draft or AI-improved answers to interview questions."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_answers",
    )
    question = models.ForeignKey(
        InterviewQuestion,
        on_delete=models.SET_NULL,
        related_name="user_answers",
        blank=True,
        null=True,
    )
    custom_question = models.TextField(blank=True, null=True)
    draft_answer = models.TextField(blank=True, null=True)
    ai_improved_answer = models.TextField(blank=True, null=True)
    is_ai_generated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_answers"
        ordering = ["-updated_at"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(question__isnull=False)
                    | models.Q(custom_question__isnull=False)
                ),
                name="question_or_custom_question",
            )
        ]

    def __str__(self):
        return f"Answer for user {self.user_id}"


class ChatSession(models.Model):
    """Chat session with the AI career assistant."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_sessions",
    )
    title = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "chat_sessions"
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title or str(self.id)


class ChatMessageRole(models.TextChoices):
    USER = "user", "User"
    ASSISTANT = "assistant", "Assistant"
    SYSTEM = "system", "System"


class ChatMessage(models.Model):
    """Single message in a chat session."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(
        max_length=20,
        choices=ChatMessageRole.choices,
    )
    content = models.TextField()
    token_count = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chat_messages"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["session", "created_at"]),
        ]

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."


class AIOutputType(models.TextChoices):
    COVER_LETTER = "cover_letter", "Cover Letter"
    TAILORED_CV = "tailored_cv", "Tailored CV"
    QUESTION_ANSWER = "question_answer", "Question Answer"


class AIOutput(models.Model):
    """Stored AI-generated content for retrieval and reuse."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_outputs",
    )
    type = models.CharField(
        max_length=30,
        choices=AIOutputType.choices,
    )
    job_description = models.ForeignKey(
        JobDescription,
        on_delete=models.SET_NULL,
        related_name="ai_outputs",
        blank=True,
        null=True,
    )
    application = models.ForeignKey(
        "tracker.Application",
        on_delete=models.SET_NULL,
        related_name="ai_outputs",
        blank=True,
        null=True,
    )
    content = models.TextField()
    prompt_snapshot = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_outputs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "type"]),
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.get_type_display()} ({self.user_id})"
