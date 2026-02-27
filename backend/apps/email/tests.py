"""Tests for email webhook API and extraction (EML-01–04)."""

import json
from django.test import Client, TestCase
from django.contrib.auth import get_user_model

from apps.email.extraction import extract_job_info
from apps.notifications.models import Notification
from apps.tracker.models import Application, ApplicationStatus
from apps.users.models import TrustedSender


class EmailWebhookTest(TestCase):
    """Tests for inbound email webhook (EML-01, EML-02)."""

    def setUp(self):
        self.client = Client()
        self.User = get_user_model()

    def _post_webhook(self, sender: str, recipient: str):
        return self.client.post(
            "/api/email/webhook",
            data=json.dumps({"sender": sender, "recipient": recipient}),
            content_type="application/json",
        )

    def test_webhook_accepts_post_returns_200(self):
        """POST /api/email/webhook with sender/recipient returns 200."""
        response = self._post_webhook("any@example.com", "fwd@example.com")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIs(data["received"], True)
        self.assertIs(data["verified"], False)

    def test_webhook_verified_when_sender_trusted(self):
        """When recipient is user's forwarding_address and sender is trusted, verified is True."""
        user = self.User.objects.create_user(
            email="u@example.com",
            forwarding_address="inbound@example.com",
            password="testpass123",
        )
        TrustedSender.objects.create(user=user, sender_email="jobs@company.com")
        response = self._post_webhook("jobs@company.com", "inbound@example.com")
        self.assertEqual(response.status_code, 200)
        self.assertIs(response.json()["verified"], True)

    def test_webhook_unverified_when_sender_not_trusted(self):
        """When recipient is user's forwarding_address but sender not in trusted_senders, verified is False."""
        self.User.objects.create_user(
            email="u@example.com",
            forwarding_address="inbound@example.com",
            password="testpass123",
        )
        response = self._post_webhook("stranger@example.com", "inbound@example.com")
        self.assertEqual(response.status_code, 200)
        self.assertIs(response.json()["verified"], False)

    def test_webhook_unverified_unknown_recipient(self):
        """When recipient is not any user's forwarding_address, verified is False."""
        response = self._post_webhook("any@example.com", "nobody@example.com")
        self.assertEqual(response.status_code, 200)
        self.assertIs(response.json()["verified"], False)

    def _post_webhook_with_content(self, sender: str, recipient: str, subject: str = "", body: str = ""):
        payload = {"sender": sender, "recipient": recipient}
        if subject:
            payload["subject"] = subject
        if body:
            payload["body"] = body
        return self.client.post(
            "/api/email/webhook",
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_webhook_returns_extracted_when_verified_and_content(self):
        """When verified and subject/body provided, response includes extracted company, job_title, date."""
        user = self.User.objects.create_user(
            email="u@example.com",
            forwarding_address="inbound@example.com",
            password="testpass123",
        )
        TrustedSender.objects.create(user=user, sender_email="jobs@company.com")
        response = self._post_webhook_with_content(
            "jobs@company.com",
            "inbound@example.com",
            subject="Application at Acme Corp",
            body="Position: Software Engineer\nApplied on 2025-02-20",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIs(data["verified"], True)
        self.assertIn("extracted", data)
        self.assertEqual(data["extracted"]["company_name"], "Acme Corp")
        self.assertEqual(data["extracted"]["job_title"], "Software Engineer")
        self.assertEqual(data["extracted"]["date_applied"], "2025-02-20T00:00:00")

    def test_webhook_creates_application_when_extracted_has_company_and_title(self):
        """EML-04: Verified + extracted company/job_title creates Application with status Applied and notification."""
        user = self.User.objects.create_user(
            email="u@example.com",
            forwarding_address="inbound@example.com",
            password="testpass123",
        )
        TrustedSender.objects.create(user=user, sender_email="jobs@company.com")
        response = self._post_webhook_with_content(
            "jobs@company.com",
            "inbound@example.com",
            subject="Application at Acme Corp",
            body="Position: Software Engineer\nApplied on 2025-02-20",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("application_id", data)
        app = Application.objects.get(pk=data["application_id"])
        self.assertEqual(app.user_id, user.id)
        self.assertEqual(app.company_name, "Acme Corp")
        self.assertEqual(app.job_title, "Software Engineer")
        self.assertEqual(app.status, ApplicationStatus.APPLIED)
        self.assertEqual(app.source, "Email")
        notifications = Notification.objects.filter(user=user, related_entity_id=app.id)
        self.assertEqual(notifications.count(), 1)
        self.assertEqual(notifications.get().type, "application_created")

    def test_webhook_no_application_when_extracted_missing_company_or_title(self):
        """When extraction has no company or job_title, no Application is created."""
        user = self.User.objects.create_user(
            email="u2@example.com",
            forwarding_address="inbound2@example.com",
            password="testpass123",
        )
        TrustedSender.objects.create(user=user, sender_email="hr@other.com")
        response = self._post_webhook_with_content(
            "hr@other.com",
            "inbound2@example.com",
            body="We received your submission. Date: 2025-02-20.",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertNotIn("application_id", data)
        self.assertEqual(Application.objects.filter(user=user).count(), 0)


class ExtractionTest(TestCase):
    """Tests for extract_job_info (EML-03)."""

    def test_extract_company_at_pattern(self):
        """Extracts company from 'Application at Company Name'."""
        out = extract_job_info(subject="Application at Acme Corp", body="")
        self.assertEqual(out["company_name"], "Acme Corp")

    def test_extract_job_title_position_pattern(self):
        """Extracts job title from 'Position: Title'."""
        out = extract_job_info(body="Position: Software Engineer")
        self.assertEqual(out["job_title"], "Software Engineer")

    def test_extract_date_iso(self):
        """Extracts date from ISO format."""
        out = extract_job_info(body="Applied 2025-02-20")
        self.assertEqual(out["date_applied"], "2025-02-20T00:00:00")

    def test_extract_empty_returns_nones(self):
        """Empty input returns None for all fields."""
        out = extract_job_info(subject="", body="")
        self.assertIsNone(out["company_name"])
        self.assertIsNone(out["job_title"])
        self.assertIsNone(out["date_applied"])
