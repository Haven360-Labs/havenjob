"""Tests for users API."""

import json
from django.test import Client, TestCase
from django.contrib.auth import get_user_model


class RegistrationAPITest(TestCase):
    """Tests for POST /api/users/register (AUTH-02)."""

    def setUp(self):
        self.client = Client()
        self.User = get_user_model()

    def test_register_success(self):
        """Registration with valid payload creates user and returns 201; password is hashed."""
        payload = {
            "email": "new@example.com",
            "forwarding_address": "new-fwd@example.com",
            "password": "securepass123",
            "full_name": "New User",
        }
        response = self.client.post(
            "/api/users/register",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["email"], "new@example.com")
        self.assertEqual(data["forwarding_address"], "new-fwd@example.com")
        self.assertIn("id", data)
        user = self.User.objects.get(email="new@example.com")
        self.assertEqual(user.full_name, "New User")
        self.assertNotEqual(user.password, "securepass123")
        self.assertTrue(user.check_password("securepass123"))

    def test_register_duplicate_email_400(self):
        """Registration with existing email returns 400."""
        self.User.objects.create_user(
            email="existing@example.com",
            forwarding_address="existing-fwd@example.com",
            password="testpass123",
        )
        response = self.client.post(
            "/api/users/register",
            data=json.dumps({
                "email": "existing@example.com",
                "forwarding_address": "other-fwd@example.com",
                "password": "securepass123",
            }),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.json().get("detail", "").lower())

    def test_register_duplicate_forwarding_address_400(self):
        """Registration with existing forwarding_address returns 400."""
        self.User.objects.create_user(
            email="one@example.com",
            forwarding_address="fwd@example.com",
            password="testpass123",
        )
        response = self.client.post(
            "/api/users/register",
            data=json.dumps({
                "email": "two@example.com",
                "forwarding_address": "fwd@example.com",
                "password": "securepass123",
            }),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("forwarding", response.json().get("detail", "").lower())

    def test_register_generates_forwarding_address_when_omitted(self):
        """ONB-01: When forwarding_address is omitted, a unique @havenjob.app address is generated."""
        response = self.client.post(
            "/api/users/register",
            data=json.dumps({
                "email": "auto@example.com",
                "password": "securepass123",
            }),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("forwarding_address", data)
        addr = data["forwarding_address"]
        self.assertTrue(addr.endswith("@havenjob.app"), f"Expected @havenjob.app, got {addr}")
        user = self.User.objects.get(email="auto@example.com")
        self.assertEqual(user.forwarding_address, addr)


class LoginAPITest(TestCase):
    """Tests for POST /api/users/login and GET /api/users/me (AUTH-04)."""

    def setUp(self):
        self.client = Client()
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email="login@example.com",
            forwarding_address="login-fwd@example.com",
            password="testpass123",
        )

    def test_login_success(self):
        """Valid email/password returns 200 and session; /me returns user."""
        response = self.client.post(
            "/api/users/login",
            data=json.dumps({"email": "login@example.com", "password": "testpass123"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["email"], "login@example.com")
        me_response = self.client.get("/api/users/me")
        self.assertEqual(me_response.status_code, 200)
        self.assertEqual(me_response.json()["email"], "login@example.com")

    def test_login_invalid_password_401(self):
        """Invalid password returns 401."""
        response = self.client.post(
            "/api/users/login",
            data=json.dumps({"email": "login@example.com", "password": "wrong"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

    def test_login_unknown_email_401(self):
        """Unknown email returns 401."""
        response = self.client.post(
            "/api/users/login",
            data=json.dumps({"email": "unknown@example.com", "password": "testpass123"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

    def test_me_unauthorized_401(self):
        """GET /me without session returns 401."""
        response = self.client.get("/api/users/me")
        self.assertEqual(response.status_code, 401)

    def test_me_returns_forwarding_and_onboarding(self):
        """GET /me returns forwarding_address and onboarding_completed."""
        self.client.force_login(self.user)
        response = self.client.get("/api/users/me")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("forwarding_address", data)
        self.assertIn("onboarding_completed", data)
        self.assertEqual(data["forwarding_address"], "login-fwd@example.com")
        self.assertFalse(data["onboarding_completed"])


class MePatchAPITest(TestCase):
    """Tests for PATCH /api/users/me."""

    def setUp(self):
        self.client = Client()
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email="patch@example.com",
            forwarding_address="patch-fwd@example.com",
            password="testpass123",
        )

    def test_patch_me_unauthorized(self):
        response = self.client.patch(
            "/api/users/me",
            data=json.dumps({"full_name": "Test"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

    def test_patch_me_updates_full_name_and_onboarding(self):
        self.client.force_login(self.user)
        response = self.client.patch(
            "/api/users/me",
            data=json.dumps({"full_name": "Jane Doe", "target_role": "Engineer", "onboarding_completed": True}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["full_name"], "Jane Doe")
        self.assertEqual(data["target_role"], "Engineer")
        self.assertTrue(data["onboarding_completed"])
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, "Jane Doe")
        self.assertTrue(self.user.onboarding_completed)


class TrustedSendersAPITest(TestCase):
    """Tests for GET/POST /api/users/trusted-senders."""

    def setUp(self):
        self.client = Client()
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email="ts@example.com",
            forwarding_address="ts-fwd@example.com",
            password="testpass123",
        )

    def test_list_trusted_senders_unauthorized(self):
        response = self.client.get("/api/users/trusted-senders")
        self.assertEqual(response.status_code, 401)

    def test_list_trusted_senders_empty(self):
        self.client.force_login(self.user)
        response = self.client.get("/api/users/trusted-senders")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_add_trusted_sender_success(self):
        self.client.force_login(self.user)
        response = self.client.post(
            "/api/users/trusted-senders",
            data=json.dumps({"sender_email": "noreply@jobs.com", "label": "Jobs"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["sender_email"], "noreply@jobs.com")
        self.assertEqual(data["label"], "Jobs")
        list_res = self.client.get("/api/users/trusted-senders")
        self.assertEqual(len(list_res.json()), 1)

    def test_add_trusted_sender_duplicate_400(self):
        from apps.users.models import TrustedSender

        TrustedSender.objects.create(user=self.user, sender_email="noreply@jobs.com")
        self.client.force_login(self.user)
        response = self.client.post(
            "/api/users/trusted-senders",
            data=json.dumps({"sender_email": "noreply@jobs.com"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
