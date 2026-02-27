import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.tracker.models import Application, ApplicationStatus, ApplicationStatusHistory, StatusChangedBy


class TrackerAPITest(TestCase):
    """Tests for tracker API endpoints."""

    def setUp(self):
        self.client = Client()
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email="api@example.com",
            forwarding_address="api-fwd@example.com",
            password="testpass123",
        )

    def test_create_application_unauthorized(self):
        """POST /api/tracker without auth returns 401."""
        response = self.client.post(
            "/api/tracker",
            data=json.dumps(
                {
                    "company_name": "X",
                    "job_title": "Y",
                    "date_applied": "2026-02-23T12:00:00Z",
                    "status": "Applied",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

    def test_create_application_success(self):
        """POST /api/tracker with auth creates application and returns 201."""
        self.client.force_login(self.user)
        payload = {
            "company_name": "Acme Inc",
            "job_title": "Engineer",
            "date_applied": "2026-02-23T14:00:00Z",
            "status": "Applied",
            "source": "Website",
            "notes": "Test note",
        }
        response = self.client.post(
            "/api/tracker",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["company_name"], "Acme Inc")
        self.assertEqual(data["job_title"], "Engineer")
        self.assertEqual(data["status"], "Applied")
        self.assertIn("id", data)
        self.assertEqual(Application.objects.filter(user=self.user).count(), 1)

    def test_get_application_unauthorized(self):
        """GET /api/tracker/{id} without auth returns 401."""
        app = Application.objects.create(
            user=self.user,
            company_name="Co",
            job_title="Job",
            date_applied=timezone.now(),
            status=ApplicationStatus.APPLIED,
        )
        response = self.client.get(f"/api/tracker/{app.id}")
        self.assertEqual(response.status_code, 401)

    def test_get_application_not_found(self):
        """GET /api/tracker/{id} with non-existent id returns 404."""
        import uuid

        self.client.force_login(self.user)
        response = self.client.get(f"/api/tracker/{uuid.uuid4()}")
        self.assertEqual(response.status_code, 404)

    def test_get_application_forbidden(self):
        """GET /api/tracker/{id} for another user's application returns 403."""
        other = self.User.objects.create_user(
            email="other@example.com",
            forwarding_address="other-fwd@example.com",
            password="testpass123",
        )
        app = Application.objects.create(
            user=other,
            company_name="Co",
            job_title="Job",
            date_applied=timezone.now(),
            status=ApplicationStatus.APPLIED,
        )
        self.client.force_login(self.user)
        response = self.client.get(f"/api/tracker/{app.id}")
        self.assertEqual(response.status_code, 403)

    def test_get_application_success(self):
        """GET /api/tracker/{id} returns application when owned by user."""
        app = Application.objects.create(
            user=self.user,
            company_name="Detail Co",
            job_title="Senior Dev",
            date_applied=timezone.now(),
            status=ApplicationStatus.UNDER_REVIEW,
            notes="Follow up next week",
        )
        self.client.force_login(self.user)
        response = self.client.get(f"/api/tracker/{app.id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["company_name"], "Detail Co")
        self.assertEqual(data["job_title"], "Senior Dev")
        self.assertEqual(data["status"], "Under Review")
        self.assertEqual(data["notes"], "Follow up next week")

    def test_list_applications_unauthorized(self):
        """GET /api/tracker without auth returns 401."""
        response = self.client.get("/api/tracker")
        self.assertEqual(response.status_code, 401)

    def test_list_applications_sorted_by_date(self):
        """GET /api/tracker returns user applications sorted by date_applied descending."""
        self.client.force_login(self.user)
        Application.objects.create(
            user=self.user,
            company_name="Older Co",
            job_title="Dev",
            date_applied=timezone.now() - timezone.timedelta(days=2),
            status=ApplicationStatus.APPLIED,
        )
        Application.objects.create(
            user=self.user,
            company_name="Newer Co",
            job_title="Engineer",
            date_applied=timezone.now() - timezone.timedelta(days=1),
            status=ApplicationStatus.APPLIED,
        )
        response = self.client.get("/api/tracker")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["company_name"], "Newer Co")
        self.assertEqual(data[1]["company_name"], "Older Co")

    def test_update_status_unauthorized(self):
        """PATCH /api/tracker/{id} without auth returns 401."""
        app = Application.objects.create(
            user=self.user,
            company_name="Co",
            job_title="Job",
            date_applied=timezone.now(),
            status=ApplicationStatus.APPLIED,
        )
        response = self.client.patch(
            f"/api/tracker/{app.id}",
            data=json.dumps({"status": "Under Review"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

    def test_update_status_not_found(self):
        """PATCH with non-existent application id returns 404."""
        import uuid

        self.client.force_login(self.user)
        response = self.client.patch(
            f"/api/tracker/{uuid.uuid4()}",
            data=json.dumps({"status": "Under Review"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)

    def test_update_status_forbidden(self):
        """PATCH another user's application returns 403."""
        other = self.User.objects.create_user(
            email="other@example.com",
            forwarding_address="other-fwd@example.com",
            password="testpass123",
        )
        app = Application.objects.create(
            user=other,
            company_name="Co",
            job_title="Job",
            date_applied=timezone.now(),
            status=ApplicationStatus.APPLIED,
        )
        self.client.force_login(self.user)
        response = self.client.patch(
            f"/api/tracker/{app.id}",
            data=json.dumps({"status": "Under Review"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_update_status_success_and_logs_history(self):
        """PATCH with new status updates application and creates status history entry."""
        app = Application.objects.create(
            user=self.user,
            company_name="Co",
            job_title="Job",
            date_applied=timezone.now(),
            status=ApplicationStatus.APPLIED,
        )
        self.client.force_login(self.user)
        response = self.client.patch(
            f"/api/tracker/{app.id}",
            data=json.dumps({"status": "Under Review"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "Under Review")
        app.refresh_from_db()
        self.assertEqual(app.status, ApplicationStatus.UNDER_REVIEW)
        history = ApplicationStatusHistory.objects.filter(application=app).order_by("changed_at")
        self.assertEqual(history.count(), 1)
        self.assertEqual(history.get().old_status, ApplicationStatus.APPLIED)
        self.assertEqual(history.get().new_status, ApplicationStatus.UNDER_REVIEW)
        self.assertEqual(history.get().changed_by, StatusChangedBy.USER)

    def test_update_status_idempotent_same_status(self):
        """PATCH with same status returns 200 but does not create duplicate history."""
        app = Application.objects.create(
            user=self.user,
            company_name="Co",
            job_title="Job",
            date_applied=timezone.now(),
            status=ApplicationStatus.APPLIED,
        )
        self.client.force_login(self.user)
        response = self.client.patch(
            f"/api/tracker/{app.id}",
            data=json.dumps({"status": "Applied"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ApplicationStatusHistory.objects.filter(application=app).count(), 0)


class ApplicationModelTest(TestCase):
    """Tests for the Application model (applications schema)."""

    def test_application_has_required_columns(self):
        """Application model has company, title, date, status, source, notes, user_id."""
        User = get_user_model()
        user = User.objects.create_user(
            email="test@example.com",
            forwarding_address="fwd@example.com",
            password="testpass123",
        )
        app = Application.objects.create(
            user=user,
            company_name="Acme Corp",
            job_title="Software Engineer",
            date_applied=timezone.now(),
            status=ApplicationStatus.APPLIED,
            source="LinkedIn",
            notes="Referred by Jane",
        )
        self.assertEqual(app.company_name, "Acme Corp")
        self.assertEqual(app.job_title, "Software Engineer")
        self.assertEqual(app.status, ApplicationStatus.APPLIED)
        self.assertEqual(app.source, "LinkedIn")
        self.assertEqual(app.notes, "Referred by Jane")
        self.assertEqual(app.user_id, user.id)
