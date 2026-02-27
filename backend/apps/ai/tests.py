"""Tests for AI app API."""

import json
from io import BytesIO
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from apps.ai.cv_parsing import extract_cv_text, extract_text_from_pdf
from apps.ai.models import CVDocument


class CVParsingTest(TestCase):
    """Tests for CV text extraction."""

    def test_extract_text_from_pdf_invalid_returns_none(self):
        """Invalid PDF bytes return None."""
        self.assertIsNone(extract_text_from_pdf(BytesIO(b"not a pdf")))

    def test_extract_text_from_pdf_valid_blank_returns_empty_or_none(self):
        """Valid blank PDF returns empty string or None."""
        from pypdf import PdfWriter

        w = PdfWriter()
        w.add_blank_page(100, 100)
        buf = BytesIO()
        w.write(buf)
        buf.seek(0)
        result = extract_text_from_pdf(buf)
        self.assertTrue(result is None or result.strip() == "")

    def test_extract_cv_text_unsupported_type_returns_none(self):
        """Unsupported content type returns None."""
        self.assertIsNone(extract_cv_text("text/plain", BytesIO(b"x")))


class CVUploadAPITest(TestCase):
    """Tests for CV upload endpoint."""

    def setUp(self):
        self.client = Client()
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email="cv@example.com",
            forwarding_address="cv-fwd@example.com",
            password="testpass123",
        )

    def test_cv_upload_unauthorized(self):
        """POST /api/ai/cv/upload without auth returns 401."""
        f = SimpleUploadedFile("resume.pdf", b"fake pdf", content_type="application/pdf")
        response = self.client.post("/api/ai/cv/upload", {"file": f}, format="multipart")
        self.assertEqual(response.status_code, 401)

    def test_cv_upload_no_file(self):
        """POST /api/ai/cv/upload with no file returns 400."""
        self.client.force_login(self.user)
        response = self.client.post("/api/ai/cv/upload", {}, format="multipart")
        self.assertEqual(response.status_code, 400)
        self.assertIn("detail", response.json())

    def test_cv_upload_invalid_type(self):
        """POST /api/ai/cv/upload with disallowed type returns 400."""
        self.client.force_login(self.user)
        f = SimpleUploadedFile("resume.txt", b"text", content_type="text/plain")
        response = self.client.post("/api/ai/cv/upload", {"file": f}, format="multipart")
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("Invalid file type", data.get("detail", ""))

    def test_cv_upload_success(self):
        """POST /api/ai/cv/upload with PDF creates CVDocument and returns 201."""
        self.client.force_login(self.user)
        content = b"%PDF-1.4 fake pdf content"
        f = SimpleUploadedFile("resume.pdf", content, content_type="application/pdf")
        response = self.client.post("/api/ai/cv/upload", {"file": f}, format="multipart")
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["file_name"], "resume.pdf")
        self.assertTrue(data["is_primary"])
        self.assertIn("id", data)
        self.assertIn("file_url", data)
        self.assertIn("uploaded_at", data)
        doc = CVDocument.objects.get(user=self.user)
        self.assertEqual(doc.file_name, "resume.pdf")
        self.assertTrue(doc.is_primary)

    def test_cv_upload_parses_valid_pdf(self):
        """Uploaded valid PDF is parsed; doc is created (parsed_text may be empty for blank PDF)."""
        from io import BytesIO
        from pypdf import PdfWriter

        self.client.force_login(self.user)
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        buf = BytesIO()
        writer.write(buf)
        pdf_bytes = buf.getvalue()
        f = SimpleUploadedFile(
            "resume.pdf", pdf_bytes, content_type="application/pdf"
        )
        response = self.client.post(
            "/api/ai/cv/upload", {"file": f}, format="multipart"
        )
        self.assertEqual(response.status_code, 201)
        doc = CVDocument.objects.get(user=self.user)
        self.assertEqual(doc.file_name, "resume.pdf")
        # Parsing runs; blank PDF may yield None or empty string
        self.assertTrue(doc.parsed_text is None or isinstance(doc.parsed_text, str))


class CoverLetterPromptTest(TestCase):
    """Tests for cover letter system prompt."""

    def test_build_cover_letter_system_prompt_includes_profile_and_jd(self):
        """Prompt contains profile context and job description."""
        from apps.ai.services import build_cover_letter_system_prompt

        profile = "Name: Jane Doe\nTarget role: Software Engineer"
        jd = "We are looking for a Python developer with 3+ years experience."
        prompt = build_cover_letter_system_prompt(profile, jd)
        self.assertIn("Jane Doe", prompt)
        self.assertIn("Software Engineer", prompt)
        self.assertIn("Python developer", prompt)
        self.assertIn("CANDIDATE PROFILE", prompt)
        self.assertIn("JOB DESCRIPTION", prompt)

    def test_build_cover_letter_system_prompt_tone_formal(self):
        """Formal tone instruction is included."""
        from apps.ai.services import build_cover_letter_system_prompt

        prompt = build_cover_letter_system_prompt("Profile", "JD", tone="formal")
        self.assertIn("formal", prompt.lower())
        self.assertIn("professional", prompt.lower())

    def test_build_cover_letter_system_prompt_tone_enthusiastic(self):
        """Enthusiastic tone instruction is included."""
        from apps.ai.services import build_cover_letter_system_prompt

        prompt = build_cover_letter_system_prompt("Profile", "JD", tone="enthusiastic")
        self.assertIn("enthusiastic", prompt.lower())


class LLMServiceTest(TestCase):
    """Tests for LLM integration service."""

    def test_llm_service_complete_returns_provider_response(self):
        """LLMService.complete delegates to provider and returns reply text."""
        from apps.ai.services import LLMService
        from providers.llm.base import LLMProvider

        class MockProvider(LLMProvider):
            def complete(self, messages, *, system_prompt=None, max_tokens=2048):
                return "Mocked reply"

        service = LLMService(llm=MockProvider())
        out = service.complete([{"role": "user", "content": "Hi"}])
        self.assertEqual(out, "Mocked reply")

    def test_get_llm_returns_openai_provider_by_default(self):
        """get_llm() with no provider returns OpenAI provider."""
        from providers.llm.factory import get_llm
        from providers.llm.openai_provider import OpenAIProvider

        llm = get_llm()
        self.assertIsInstance(llm, OpenAIProvider)

    def test_get_llm_returns_anthropic_when_requested(self):
        """get_llm(provider='anthropic') returns Anthropic provider."""
        from providers.llm.factory import get_llm
        from providers.llm.anthropic_provider import AnthropicProvider

        llm = get_llm(provider="anthropic")
        self.assertIsInstance(llm, AnthropicProvider)


class ChatAPITest(TestCase):
    """Tests for chat endpoints."""

    def setUp(self):
        self.client = Client()
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email="chat@example.com",
            forwarding_address="chat-fwd@example.com",
            password="testpass123",
        )

    def test_chat_create_session_unauthorized(self):
        """POST /api/ai/chat/sessions without auth returns 401."""
        response = self.client.post("/api/ai/chat/sessions", {})
        self.assertEqual(response.status_code, 401)

    def test_chat_create_session_success(self):
        """POST /api/ai/chat/sessions creates session and returns 201."""
        self.client.force_login(self.user)
        response = self.client.post(
            "/api/ai/chat/sessions",
            {},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("id", data)
        self.assertIn("created_at", data)
        from apps.ai.models import ChatSession

        self.assertEqual(ChatSession.objects.filter(user=self.user).count(), 1)

    def test_chat_list_sessions_unauthorized(self):
        """GET /api/ai/chat/sessions without auth returns 401."""
        response = self.client.get("/api/ai/chat/sessions")
        self.assertEqual(response.status_code, 401)

    def test_chat_list_sessions_returns_mine(self):
        """GET /api/ai/chat/sessions returns user's sessions."""
        from apps.ai.models import ChatSession

        ChatSession.objects.create(user=self.user)
        self.client.force_login(self.user)
        response = self.client.get("/api/ai/chat/sessions")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)

    def test_chat_list_messages_returns_messages(self):
        """GET /api/ai/chat/sessions/{id}/messages returns session messages."""
        from apps.ai.models import ChatMessage, ChatSession

        session = ChatSession.objects.create(user=self.user)
        ChatMessage.objects.create(session=session, role="user", content="Hi")
        ChatMessage.objects.create(session=session, role="assistant", content="Hello")
        self.client.force_login(self.user)
        response = self.client.get(f"/api/ai/chat/sessions/{session.id}/messages")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["role"], "user")
        self.assertEqual(data[1]["role"], "assistant")

    def test_chat_send_message_unauthorized(self):
        """POST .../messages without auth returns 401."""
        from apps.ai.models import ChatSession

        session = ChatSession.objects.create(user=self.user)
        response = self.client.post(
            f"/api/ai/chat/sessions/{session.id}/messages",
            {"content": "Hello"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

    def test_chat_send_message_streams_with_mocked_llm(self):
        """POST .../messages with auth calls LLM and streams response (mocked)."""
        from apps.ai.models import ChatMessage, ChatSession

        session = ChatSession.objects.create(user=self.user)
        self.client.force_login(self.user)
        with patch("apps.ai.api.LLMService") as MockLLMService:
            mock_instance = MockLLMService.return_value
            mock_instance.stream_complete.return_value = iter(["Mocked ", "reply"])
            response = self.client.post(
                f"/api/ai/chat/sessions/{session.id}/messages",
                {"content": "Hello"},
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), b"Mocked reply")
        user_msg = ChatMessage.objects.get(session=session, role="user")
        self.assertEqual(user_msg.content, "Hello")
        assistant_msg = ChatMessage.objects.get(session=session, role="assistant")
        self.assertEqual(assistant_msg.content, "Mocked reply")


class ImproveAnswerPromptTest(TestCase):
    """Tests for improve-answer system prompt."""

    def test_build_improve_answer_system_prompt_includes_star_and_question(self):
        """Prompt mentions STAR and includes question when provided."""
        from apps.ai.services import build_improve_answer_system_prompt

        prompt = build_improve_answer_system_prompt("Tell me about a conflict.")
        self.assertIn("STAR", prompt)
        self.assertIn("Situation", prompt)
        self.assertIn("Task", prompt)
        self.assertIn("Action", prompt)
        self.assertIn("Result", prompt)
        self.assertIn("Tell me about a conflict", prompt)

    def test_build_improve_answer_system_prompt_works_without_question(self):
        """Prompt builds when question is None or empty."""
        from apps.ai.services import build_improve_answer_system_prompt

        prompt = build_improve_answer_system_prompt(None)
        self.assertIn("STAR", prompt)
        prompt2 = build_improve_answer_system_prompt("")
        self.assertIn("STAR", prompt2)


class ImproveAnswerAPITest(TestCase):
    """Tests for improve-answer endpoint."""

    def setUp(self):
        self.client = Client()
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email="qa@example.com",
            forwarding_address="qa-fwd@example.com",
            password="testpass123",
        )

    def test_improve_answer_unauthorized(self):
        """POST /api/ai/improve-answer without auth returns 401."""
        response = self.client.post(
            "/api/ai/improve-answer",
            {"draft_answer": "I fixed the bug."},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

    def test_improve_answer_no_draft(self):
        """POST with empty draft_answer returns 400."""
        self.client.force_login(self.user)
        response = self.client.post(
            "/api/ai/improve-answer",
            {"draft_answer": ""},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("detail", response.json())

    def test_improve_answer_returns_improved_with_mocked_llm(self):
        """POST with draft returns 200 and improved_answer (mocked LLM)."""
        self.client.force_login(self.user)
        with patch("apps.ai.api.LLMService") as MockLLMService:
            mock_instance = MockLLMService.return_value
            mock_instance.complete.return_value = "STAR-formatted improved text."
            response = self.client.post(
                "/api/ai/improve-answer",
                {"draft_answer": "I fixed a bug by testing.", "question": "Tell me about a bug you fixed."},
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("improved_answer", data)
        self.assertEqual(data["improved_answer"], "STAR-formatted improved text.")

    def test_improve_answer_saves_to_user_answer_when_id_given(self):
        """When user_answer_id is provided and valid, result is saved to UserAnswer."""
        from apps.ai.models import InterviewQuestion, UserAnswer

        self.client.force_login(self.user)
        q = InterviewQuestion.objects.create(
            category="Behavioural",
            question_type="behavioural",
            question="Tell me about a challenge.",
        )
        ua = UserAnswer.objects.create(
            user=self.user,
            question=q,
            draft_answer="We had a tight deadline.",
        )
        with patch("apps.ai.api.LLMService") as MockLLMService:
            mock_instance = MockLLMService.return_value
            mock_instance.complete.return_value = "Situation: ... Task: ... Action: ... Result: ..."
            response = self.client.post(
                "/api/ai/improve-answer",
                {"draft_answer": "We had a tight deadline.", "user_answer_id": str(ua.id)},
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 200)
        ua.refresh_from_db()
        self.assertEqual(ua.ai_improved_answer, "Situation: ... Task: ... Action: ... Result: ...")
        self.assertTrue(ua.is_ai_generated)


class CoverLetterAPITest(TestCase):
    """Tests for cover-letter endpoint."""

    def setUp(self):
        self.client = Client()
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email="cl@example.com",
            forwarding_address="cl-fwd@example.com",
            password="testpass123",
        )

    def test_cover_letter_unauthorized(self):
        """POST /api/ai/cover-letter without auth returns 401."""
        response = self.client.post(
            "/api/ai/cover-letter",
            {"job_description": "Senior Engineer at Acme."},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

    def test_cover_letter_empty_jd(self):
        """POST with empty job_description returns 400."""
        self.client.force_login(self.user)
        response = self.client.post(
            "/api/ai/cover-letter",
            {"job_description": ""},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("detail", response.json())

    def test_cover_letter_returns_generated_with_mocked_llm(self):
        """POST with job_description returns 200 and cover_letter (mocked LLM)."""
        self.client.force_login(self.user)
        with patch("apps.ai.api.LLMService") as MockLLMService:
            mock_instance = MockLLMService.return_value
            mock_instance.complete.return_value = "Dear Hiring Manager,\n\nI am writing to apply..."
            response = self.client.post(
                "/api/ai/cover-letter",
                {"job_description": "Senior Software Engineer at Acme Corp.", "tone": "formal"},
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("cover_letter", data)
        self.assertIn("Dear Hiring Manager", data["cover_letter"])


class InterviewQAAPITest(TestCase):
    """Tests for interview questions and user answers endpoints."""

    def setUp(self):
        self.client = Client()
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email="qa2@example.com",
            forwarding_address="qa2-fwd@example.com",
            password="testpass123",
        )

    def test_list_interview_questions_unauthorized(self):
        """GET /api/ai/interview-questions without auth returns 401."""
        response = self.client.get("/api/ai/interview-questions")
        self.assertEqual(response.status_code, 401)

    def test_list_interview_questions_empty(self):
        """GET /api/ai/interview-questions returns 200 and list (may be empty)."""
        self.client.force_login(self.user)
        response = self.client.get("/api/ai/interview-questions")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_list_interview_questions_with_data(self):
        """GET returns questions when present."""
        from apps.ai.models import InterviewQuestion

        InterviewQuestion.objects.create(
            category="Behavioural",
            question_type="behavioural",
            question="Tell me about a challenge.",
        )
        self.client.force_login(self.user)
        response = self.client.get("/api/ai/interview-questions")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["question"], "Tell me about a challenge.")
        self.assertEqual(data[0]["category"], "Behavioural")

    def test_create_user_answer_unauthorized(self):
        """POST /api/ai/user-answers without auth returns 401."""
        response = self.client.post(
            "/api/ai/user-answers",
            {"custom_question": "Why us?", "draft_answer": "Because."},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

    def test_create_user_answer_requires_question_or_custom(self):
        """POST without question_id or custom_question returns 400."""
        self.client.force_login(self.user)
        response = self.client.post(
            "/api/ai/user-answers",
            {},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_create_user_answer_with_custom_question(self):
        """POST with custom_question creates user answer and returns 201."""
        self.client.force_login(self.user)
        response = self.client.post(
            "/api/ai/user-answers",
            {"custom_question": "Why us?", "draft_answer": "I want to grow here."},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("id", data)
        self.assertEqual(data["custom_question"], "Why us?")
        self.assertEqual(data["draft_answer"], "I want to grow here.")
        from apps.ai.models import UserAnswer

        self.assertEqual(UserAnswer.objects.filter(user=self.user).count(), 1)

    def test_list_user_answers_unauthorized(self):
        """GET /api/ai/user-answers without auth returns 401."""
        response = self.client.get("/api/ai/user-answers")
        self.assertEqual(response.status_code, 401)

    def test_list_user_answers_returns_mine(self):
        """GET returns current user's answers."""
        self.client.force_login(self.user)
        response = self.client.get("/api/ai/user-answers")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])


class ProfileWorkExperienceAPITest(TestCase):
    """Tests for profile work experience API (AI-02)."""

    def setUp(self):
        self.client = Client()
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email="we@example.com",
            forwarding_address="we-fwd@example.com",
            password="testpass123",
        )

    def test_list_work_experience_unauthorized(self):
        response = self.client.get("/api/ai/profile/work-experience")
        self.assertEqual(response.status_code, 401)

    def test_list_and_create_work_experience(self):
        self.client.force_login(self.user)
        response = self.client.get("/api/ai/profile/work-experience")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])
        create = self.client.post(
            "/api/ai/profile/work-experience",
            data=json.dumps({
                "company": "Acme",
                "role": "Engineer",
                "start_date": "2024-01-01",
                "is_current": True,
            }),
            content_type="application/json",
        )
        self.assertEqual(create.status_code, 201)
        data = create.json()
        self.assertEqual(data["company"], "Acme")
        self.assertEqual(data["role"], "Engineer")
        list_resp = self.client.get("/api/ai/profile/work-experience")
        self.assertEqual(list_resp.status_code, 200)
        self.assertEqual(len(list_resp.json()), 1)


class ProfileProjectsAPITest(TestCase):
    """Tests for profile projects API (AI-02)."""

    def setUp(self):
        self.client = Client()
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email="proj@example.com",
            forwarding_address="proj-fwd@example.com",
            password="testpass123",
        )

    def test_list_projects_unauthorized(self):
        response = self.client.get("/api/ai/profile/projects")
        self.assertEqual(response.status_code, 401)

    def test_list_and_create_project(self):
        self.client.force_login(self.user)
        response = self.client.get("/api/ai/profile/projects")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])
        create = self.client.post(
            "/api/ai/profile/projects",
            data=json.dumps({
                "title": "My App",
                "description": "A web app",
            }),
            content_type="application/json",
        )
        self.assertEqual(create.status_code, 201)
        data = create.json()
        self.assertEqual(data["title"], "My App")
        list_resp = self.client.get("/api/ai/profile/projects")
        self.assertEqual(list_resp.status_code, 200)
        self.assertEqual(len(list_resp.json()), 1)
