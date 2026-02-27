"""Tests for notifications API and services."""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from apps.notifications.models import Notification, RelatedEntityType
from apps.notifications.services import notify_application_created


class NotificationsAPITest(TestCase):
    """Tests for notifications API endpoints."""

    def setUp(self):
        self.client = Client()
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email="notif@example.com",
            forwarding_address="notif-fwd@example.com",
            password="testpass123",
        )

    def test_list_notifications_unauthorized(self):
        """GET /api/notifications without auth returns 401."""
        response = self.client.get("/api/notifications")
        self.assertEqual(response.status_code, 401)

    def test_list_notifications_success(self):
        """GET /api/notifications returns user's notifications."""
        Notification.objects.create(
            user=self.user,
            type="test",
            title="Test",
            message="Body",
        )
        self.client.force_login(self.user)
        response = self.client.get("/api/notifications")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["title"], "Test")
        self.assertFalse(data[0]["is_read"])

    def test_mark_read_unauthorized(self):
        """PATCH .../notifications/{id} without auth returns 401."""
        n = Notification.objects.create(user=self.user, type="t", title="T")
        response = self.client.patch(f"/api/notifications/{n.id}")
        self.assertEqual(response.status_code, 401)

    def test_mark_read_forbidden(self):
        """PATCH with another user's notification returns 403."""
        other = self.User.objects.create_user(
            email="other@example.com",
            forwarding_address="other-fwd@example.com",
            password="testpass123",
        )
        n = Notification.objects.create(user=other, type="t", title="T")
        self.client.force_login(self.user)
        response = self.client.patch(f"/api/notifications/{n.id}")
        self.assertEqual(response.status_code, 403)

    def test_mark_read_not_found(self):
        """PATCH with non-existent notification id returns 404."""
        import uuid

        self.client.force_login(self.user)
        response = self.client.patch(f"/api/notifications/{uuid.uuid4()}")
        self.assertEqual(response.status_code, 404)

    def test_mark_read_success(self):
        """PATCH marks notification as read and returns 200."""
        n = Notification.objects.create(user=self.user, type="t", title="T", is_read=False)
        self.client.force_login(self.user)
        response = self.client.patch(f"/api/notifications/{n.id}")
        self.assertEqual(response.status_code, 200)
        n.refresh_from_db()
        self.assertTrue(n.is_read)


class NotifyApplicationCreatedTest(TestCase):
    """Tests for notify_application_created trigger (EML-06)."""

    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email="trigger@example.com",
            forwarding_address="trigger-fwd@example.com",
            password="testpass123",
        )

    def test_creates_notification_with_application_entity(self):
        """notify_application_created creates a notification linked to the application."""
        import uuid

        app_id = uuid.uuid4()
        n = notify_application_created(self.user.id, app_id)
        self.assertEqual(n.user_id, self.user.id)
        self.assertEqual(n.type, "application_created")
        self.assertEqual(n.title, "New application logged")
        self.assertEqual(n.related_entity_type, RelatedEntityType.APPLICATION)
        self.assertEqual(n.related_entity_id, app_id)
        self.assertFalse(n.is_read)
