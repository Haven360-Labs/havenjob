import uuid
from django.db import models
from django.conf import settings


class ApplicationStatus(models.TextChoices):
    APPLIED = "Applied", "Applied"
    UNDER_REVIEW = "Under Review", "Under Review"
    PHONE_SCREEN = "Phone Screen", "Phone Screen"
    INTERVIEW = "Interview", "Interview"
    OFFER = "Offer", "Offer"
    ACCEPTED = "Accepted", "Accepted"
    REJECTED = "Rejected", "Rejected"
    WITHDRAWN = "Withdrawn", "Withdrawn"


class Application(models.Model):
    """Job application record."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="applications",
    )
    company_name = models.CharField(max_length=255)
    job_title = models.CharField(max_length=255)
    date_applied = models.DateTimeField()
    deadline = models.DateTimeField(blank=True, null=True)
    follow_up_date = models.DateTimeField(blank=True, null=True)
    status = models.CharField(
        max_length=30,
        choices=ApplicationStatus.choices,
    )
    source = models.CharField(max_length=255, blank=True, null=True)
    job_url = models.URLField(max_length=2000, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    salary_min = models.IntegerField(blank=True, null=True)
    salary_max = models.IntegerField(blank=True, null=True)
    salary_currency = models.CharField(max_length=3, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    is_needs_review = models.BooleanField(default=False)
    confidence_score = models.FloatField(blank=True, null=True)
    parse_metadata = models.JSONField(default=dict, blank=True, null=True)
    raw_email_hash = models.CharField(max_length=64, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "applications"
        ordering = ["-date_applied"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["user", "-date_applied"]),
            models.Index(fields=["user", "follow_up_date"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "raw_email_hash"],
                name="unique_user_raw_email_hash",
                condition=models.Q(raw_email_hash__isnull=False),
            )
        ]

    def __str__(self):
        return f"{self.job_title} at {self.company_name}"


class StatusChangedBy(models.TextChoices):
    USER = "user", "User"
    EMAIL_PARSER = "email_parser", "Email Parser"
    SYSTEM = "system", "System"


class ApplicationStatusHistory(models.Model):
    """Audit trail of application status changes."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="status_history",
    )
    old_status = models.CharField(
        max_length=30,
        choices=ApplicationStatus.choices,
        blank=True,
        null=True,
    )
    new_status = models.CharField(
        max_length=30,
        choices=ApplicationStatus.choices,
    )
    changed_by = models.CharField(
        max_length=20,
        choices=StatusChangedBy.choices,
    )
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "application_status_history"
        ordering = ["changed_at"]
        verbose_name_plural = "Application status histories"

    def __str__(self):
        return f"{self.application_id}: {self.old_status} → {self.new_status}"
