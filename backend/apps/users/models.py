import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class AuthProvider(models.TextChoices):
    EMAIL = "email", "Email"
    GOOGLE = "google", "Google"
    LINKEDIN = "linkedin", "LinkedIn"


class SubscriptionTier(models.TextChoices):
    FREE = "free", "Free"
    CREDITS = "credits", "Credits"
    PRO = "pro", "Pro"


class ProviderType(models.TextChoices):
    LLM = "llm", "LLM"
    EMAIL_INBOUND = "email_inbound", "Email Inbound"


class ProviderName(models.TextChoices):
    OPENAI = "openai", "OpenAI"
    ANTHROPIC = "anthropic", "Anthropic"
    GMAIL = "gmail", "Gmail"
    SENDGRID = "sendgrid", "SendGrid"


class UserManager(BaseUserManager):
    def create_user(self, email, forwarding_address, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        if not forwarding_address:
            raise ValueError("Users must have a forwarding address")
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            forwarding_address=forwarding_address,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, forwarding_address, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(email, forwarding_address, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model matching HavenJob users table."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    password = models.CharField(
        max_length=128,
        db_column="hashed_password",
        blank=True,
        null=True,
    )
    auth_provider = models.CharField(
        max_length=20,
        choices=AuthProvider.choices,
        default=AuthProvider.EMAIL,
    )
    forwarding_address = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    target_role = models.CharField(max_length=255, blank=True, null=True)
    skills = models.JSONField(default=dict, blank=True, null=True)
    avatar_url = models.URLField(max_length=500, blank=True, null=True)
    onboarding_completed = models.BooleanField(default=False)
    profile_completion_percent = models.IntegerField(default=0)
    subscription_tier = models.CharField(
        max_length=20,
        choices=SubscriptionTier.choices,
        default=SubscriptionTier.FREE,
    )
    credits_balance = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["forwarding_address"]

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]

    def __str__(self):
        return self.email


class TrustedSender(models.Model):
    """Senders the user trusts for parsing job emails."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="trusted_senders",
    )
    sender_email = models.EmailField()
    label = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "trusted_senders"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "sender_email"],
                name="unique_user_sender_email",
            )
        ]
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender_email} ({self.user.email})"


class UserProviderSettings(models.Model):
    """User's LLM and email inbound provider with encrypted API key."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="provider_settings",
    )
    provider_type = models.CharField(
        max_length=20,
        choices=ProviderType.choices,
    )
    provider_name = models.CharField(
        max_length=20,
        choices=ProviderName.choices,
    )
    encrypted_api_key = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_provider_settings"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "provider_type"],
                name="unique_user_provider_type",
            )
        ]
        ordering = ["user", "provider_type"]

    def __str__(self):
        return f"{self.user.email} - {self.provider_type}:{self.provider_name}"
