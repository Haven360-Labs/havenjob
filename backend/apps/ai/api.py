import re
import uuid
from io import BytesIO

from django.core.files.storage import default_storage
from django.db import transaction
from django.http import StreamingHttpResponse
from ninja import File, Router
from ninja.files import UploadedFile

from apps.ai.cv_parsing import extract_cv_text
from apps.ai.models import (
    ChatMessage,
    ChatMessageRole,
    ChatSession,
    CVDocument,
    InterviewQuestion,
    Project,
    UserAnswer,
    WorkExperience,
)
from apps.ai.schemas import (
    ChatMessageIn,
    ChatMessageOut,
    ChatSessionOut,
    CoverLetterIn,
    CoverLetterOut,
    CVDocumentOut,
    ImproveAnswerIn,
    ImproveAnswerOut,
    InterviewQuestionOut,
    ProjectIn,
    ProjectOut,
    UserAnswerIn,
    UserAnswerOut,
    WorkExperienceIn,
    WorkExperienceOut,
)
from apps.ai.services import (
    LLMService,
    build_context,
    build_cover_letter_system_prompt,
    build_improve_answer_system_prompt,
)

router = Router(tags=["ai"])

ALLOWED_CV_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # DOCX
}
MAX_CV_SIZE_BYTES = 10 * 1024 * 1024  # 10MB


def _safe_storage_name(original_name: str, prefix: str) -> str:
    """Build a unique storage path: prefix/uuid_sanitized.ext."""
    ext = ""
    if "." in original_name:
        ext = "." + original_name.rsplit(".", 1)[-1].lower()
    safe = re.sub(r"[^\w.-]", "_", original_name[: 255 - len(ext) - 40]) or "cv"
    return f"{prefix}/{uuid.uuid4().hex}_{safe}{ext}"


@router.get("")
def ai_root(request):
    """Placeholder: AI endpoints (chat, cover letter, etc.) to be added later."""
    return {"detail": "Not implemented"}


@router.post(
    "cv/upload",
    response={201: CVDocumentOut, 400: dict, 401: dict},
)
def cv_upload(request, file: File[UploadedFile] = None):
    """
    Upload a CV (PDF or DOCX). Requires authentication.
    Stored file is set as the user's primary CV.
    """
    if not request.user.is_authenticated:
        return 401, {"detail": "Authentication required"}
    if file is None:
        return 400, {"detail": "No file provided"}
    if file.content_type not in ALLOWED_CV_CONTENT_TYPES:
        return 400, {
            "detail": "Invalid file type. Allowed: PDF, DOCX",
        }
    if file.size > MAX_CV_SIZE_BYTES:
        return 400, {
            "detail": f"File too large. Maximum size: {MAX_CV_SIZE_BYTES // (1024*1024)}MB",
        }
    user_id = request.user.id
    storage_path = _safe_storage_name(file.name, f"cv/{user_id}")
    file.open("rb")
    try:
        file_content = file.read()
        saved_name = default_storage.save(storage_path, BytesIO(file_content))
    finally:
        file.close()
    parsed_text = extract_cv_text(file.content_type, BytesIO(file_content))
    with transaction.atomic():
        CVDocument.objects.filter(user_id=user_id).update(is_primary=False)
        doc = CVDocument.objects.create(
            user_id=user_id,
            file_name=file.name[:255],
            file_url=saved_name,
            parsed_text=parsed_text,
            is_primary=True,
        )
    response_url = default_storage.url(saved_name)
    return 201, CVDocumentOut(
        id=doc.id,
        file_name=doc.file_name,
        file_url=response_url,
        is_primary=doc.is_primary,
        uploaded_at=doc.uploaded_at,
    )


# ---- Chat ----


@router.get(
    "chat/sessions",
    response={200: list[ChatSessionOut], 401: dict},
)
def chat_list_sessions(request):
    """List current user's chat sessions (newest first). Requires authentication."""
    if not request.user.is_authenticated:
        return 401, {"detail": "Authentication required"}
    qs = ChatSession.objects.filter(user=request.user).order_by("-updated_at")[:50]
    return 200, list(qs)


@router.post(
    "chat/sessions",
    response={201: ChatSessionOut, 401: dict},
)
def chat_create_session(request):
    """Create a new chat session. Requires authentication."""
    if not request.user.is_authenticated:
        return 401, {"detail": "Authentication required"}
    session = ChatSession.objects.create(user=request.user)
    return 201, session


@router.get(
    "chat/sessions/{session_id}/messages",
    response={200: list[ChatMessageOut], 401: dict, 403: dict, 404: dict},
)
def chat_list_messages(request, session_id: uuid.UUID):
    """List messages in a chat session. Requires auth; session must belong to user."""
    if not request.user.is_authenticated:
        return 401, {"detail": "Authentication required"}
    try:
        session = ChatSession.objects.get(pk=session_id)
    except ChatSession.DoesNotExist:
        return 404, {"detail": "Session not found"}
    if session.user_id != request.user.id:
        return 403, {"detail": "Forbidden"}
    qs = ChatMessage.objects.filter(session=session).order_by("created_at")
    return 200, list(qs)


@router.post(
    "chat/sessions/{session_id}/messages",
    response={200: None, 400: dict, 401: dict, 403: dict, 404: dict},
)
def chat_send_message(request, session_id: uuid.UUID, payload: ChatMessageIn):
    """
    Send a message and stream the assistant reply. Uses profile context.
    Requires authentication; session must belong to the user.
    """
    if not request.user.is_authenticated:
        return 401, {"detail": "Authentication required"}
    try:
        session = ChatSession.objects.get(pk=session_id)
    except ChatSession.DoesNotExist:
        return 404, {"detail": "Session not found"}
    if session.user_id != request.user.id:
        return 403, {"detail": "Forbidden"}
    content = (payload.content or "").strip()
    if not content:
        return 400, {"detail": "Message content is required"}

    ChatMessage.objects.create(
        session=session,
        role=ChatMessageRole.USER,
        content=content,
    )
    if not session.title:
        session.title = content[:200] if len(content) > 200 else content
        session.save(update_fields=["title", "updated_at"])

    history = [
        {"role": msg.role, "content": msg.content}
        for msg in session.messages.order_by("created_at")
    ]
    system_prompt = build_context(request.user)
    service = LLMService()
    accumulated: list[str] = []

    def stream_gen():
        nonlocal accumulated
        try:
            for chunk in service.stream_complete(
                history,
                system_prompt=system_prompt,
                max_tokens=2048,
            ):
                accumulated.append(chunk)
                yield chunk
        finally:
            if accumulated:
                ChatMessage.objects.create(
                    session=session,
                    role=ChatMessageRole.ASSISTANT,
                    content="".join(accumulated),
                )

    return StreamingHttpResponse(
        stream_gen(),
        content_type="text/plain; charset=utf-8",
    )


# ---- Cover Letter ----


@router.post(
    "cover-letter",
    response={200: CoverLetterOut, 400: dict, 401: dict},
)
def generate_cover_letter(request, payload: CoverLetterIn):
    """
    Generate a cover letter from the user's profile and the given job description.
    Requires authentication.
    """
    if not request.user.is_authenticated:
        return 401, {"detail": "Authentication required"}
    jd = (payload.job_description or "").strip()
    if not jd:
        return 400, {"detail": "Job description is required"}
    profile_context = build_context(request.user)
    system_prompt = build_cover_letter_system_prompt(
        profile_context, jd, tone=payload.tone or "formal"
    )
    messages = [{"role": "user", "content": "Please write the cover letter based on the instructions above."}]
    service = LLMService()
    text = service.complete(messages, system_prompt=system_prompt, max_tokens=1024)
    return 200, CoverLetterOut(cover_letter=text.strip())


# ---- Q&A Improvement ----


@router.post(
    "improve-answer",
    response={200: ImproveAnswerOut, 400: dict, 401: dict, 403: dict, 404: dict},
)
def improve_answer(request, payload: ImproveAnswerIn):
    """
    Send draft interview answer to LLM; returns STAR-formatted improved version.
    Optionally pass user_answer_id to save the result to that UserAnswer.
    """
    if not request.user.is_authenticated:
        return 401, {"detail": "Authentication required"}
    draft = (payload.draft_answer or "").strip()
    if not draft:
        return 400, {"detail": "draft_answer is required"}

    user_answer = None
    if payload.user_answer_id is not None:
        try:
            user_answer = UserAnswer.objects.get(pk=payload.user_answer_id)
        except UserAnswer.DoesNotExist:
            return 404, {"detail": "UserAnswer not found"}
        if user_answer.user_id != request.user.id:
            return 403, {"detail": "Forbidden"}

    system_prompt = build_improve_answer_system_prompt(payload.question)
    messages = [{"role": "user", "content": draft}]
    improved = LLMService().complete(messages, system_prompt=system_prompt, max_tokens=1024)

    if user_answer:
        user_answer.ai_improved_answer = improved
        user_answer.is_ai_generated = True
        user_answer.save(update_fields=["ai_improved_answer", "is_ai_generated", "updated_at"])

    return 200, ImproveAnswerOut(improved_answer=improved)


# ---- Interview Q&A (behavioural / standard questions + user answers) ----


@router.get(
    "interview-questions",
    response={200: list[InterviewQuestionOut], 401: dict},
)
def list_interview_questions(
    request,
    category: str | None = None,
    question_type: str | None = None,
):
    """List interview questions (optional filter by category or question_type). Requires auth."""
    if not request.user.is_authenticated:
        return 401, {"detail": "Authentication required"}
    qs = InterviewQuestion.objects.all().order_by("category", "created_at")
    if category:
        qs = qs.filter(category__iexact=category)
    if question_type:
        qs = qs.filter(question_type=question_type)
    return 200, list(qs[:100])


@router.get(
    "user-answers",
    response={200: list[UserAnswerOut], 401: dict},
)
def list_user_answers(request):
    """List the current user's answers. Requires auth."""
    if not request.user.is_authenticated:
        return 401, {"detail": "Authentication required"}
    qs = UserAnswer.objects.filter(user=request.user).order_by("-updated_at")[:50]
    return 200, list(qs)


@router.post(
    "user-answers",
    response={201: UserAnswerOut, 400: dict, 401: dict, 404: dict},
)
def create_user_answer(request, payload: UserAnswerIn):
    """Create a user answer (draft). Requires question_id or custom_question. Requires auth."""
    if not request.user.is_authenticated:
        return 401, {"detail": "Authentication required"}
    if payload.question_id is None and not (payload.custom_question and payload.custom_question.strip()):
        return 400, {"detail": "Provide question_id or custom_question"}
    if payload.question_id is not None:
        try:
            InterviewQuestion.objects.get(pk=payload.question_id)
        except InterviewQuestion.DoesNotExist:
            return 404, {"detail": "Question not found"}
    answer = UserAnswer.objects.create(
        user=request.user,
        question_id=payload.question_id,
        custom_question=payload.custom_question.strip() if payload.custom_question else None,
        draft_answer=payload.draft_answer.strip() if payload.draft_answer else None,
    )
    return 201, answer


# Profile: work experience and projects (AI-02)


@router.get(
    "profile/work-experience",
    response={200: list[WorkExperienceOut], 401: dict},
)
def list_work_experience(request):
    """List current user's work experience. Requires auth."""
    if not request.user.is_authenticated:
        return 401, {"detail": "Authentication required"}
    qs = WorkExperience.objects.filter(user=request.user).order_by("display_order", "-start_date")
    return 200, list(qs)


@router.post(
    "profile/work-experience",
    response={201: WorkExperienceOut, 401: dict},
)
def create_work_experience(request, payload: WorkExperienceIn):
    """Create work experience. Requires auth."""
    if not request.user.is_authenticated:
        return 401, {"detail": "Authentication required"}
    obj = WorkExperience.objects.create(
        user=request.user,
        company=payload.company,
        role=payload.role,
        start_date=payload.start_date,
        end_date=payload.end_date,
        is_current=payload.is_current,
        description=payload.description,
        display_order=payload.display_order,
    )
    return 201, obj


@router.get(
    "profile/work-experience/{we_id}",
    response={200: WorkExperienceOut, 401: dict, 403: dict, 404: dict},
)
def get_work_experience(request, we_id: uuid.UUID):
    """Get one work experience. Requires auth; must own."""
    if not request.user.is_authenticated:
        return 401, {"detail": "Authentication required"}
    try:
        obj = WorkExperience.objects.get(pk=we_id)
    except WorkExperience.DoesNotExist:
        return 404, {"detail": "Not found"}
    if obj.user_id != request.user.id:
        return 403, {"detail": "Forbidden"}
    return 200, obj


@router.patch(
    "profile/work-experience/{we_id}",
    response={200: WorkExperienceOut, 401: dict, 403: dict, 404: dict},
)
def update_work_experience(request, we_id: uuid.UUID, payload: WorkExperienceIn):
    """Update work experience. Requires auth; must own."""
    if not request.user.is_authenticated:
        return 401, {"detail": "Authentication required"}
    try:
        obj = WorkExperience.objects.get(pk=we_id)
    except WorkExperience.DoesNotExist:
        return 404, {"detail": "Not found"}
    if obj.user_id != request.user.id:
        return 403, {"detail": "Forbidden"}
    obj.company = payload.company
    obj.role = payload.role
    obj.start_date = payload.start_date
    obj.end_date = payload.end_date
    obj.is_current = payload.is_current
    obj.description = payload.description
    obj.display_order = payload.display_order
    obj.save()
    return 200, obj


@router.delete(
    "profile/work-experience/{we_id}",
    response={204: None, 401: dict, 403: dict, 404: dict},
)
def delete_work_experience(request, we_id: uuid.UUID):
    """Delete work experience. Requires auth; must own."""
    if not request.user.is_authenticated:
        return 401, {"detail": "Authentication required"}
    try:
        obj = WorkExperience.objects.get(pk=we_id)
    except WorkExperience.DoesNotExist:
        return 404, {"detail": "Not found"}
    if obj.user_id != request.user.id:
        return 403, {"detail": "Forbidden"}
    obj.delete()
    return 204, None


@router.get(
    "profile/projects",
    response={200: list[ProjectOut], 401: dict},
)
def list_projects(request):
    """List current user's projects. Requires auth."""
    if not request.user.is_authenticated:
        return 401, {"detail": "Authentication required"}
    qs = Project.objects.filter(user=request.user).order_by("display_order")
    return 200, list(qs)


@router.post(
    "profile/projects",
    response={201: ProjectOut, 401: dict},
)
def create_project(request, payload: ProjectIn):
    """Create project. Requires auth."""
    if not request.user.is_authenticated:
        return 401, {"detail": "Authentication required"}
    obj = Project.objects.create(
        user=request.user,
        title=payload.title,
        description=payload.description,
        technologies=payload.technologies or [],
        url=payload.url,
        display_order=payload.display_order,
    )
    return 201, obj


@router.get(
    "profile/projects/{project_id}",
    response={200: ProjectOut, 401: dict, 403: dict, 404: dict},
)
def get_project(request, project_id: uuid.UUID):
    """Get one project. Requires auth; must own."""
    if not request.user.is_authenticated:
        return 401, {"detail": "Authentication required"}
    try:
        obj = Project.objects.get(pk=project_id)
    except Project.DoesNotExist:
        return 404, {"detail": "Not found"}
    if obj.user_id != request.user.id:
        return 403, {"detail": "Forbidden"}
    return 200, obj


@router.patch(
    "profile/projects/{project_id}",
    response={200: ProjectOut, 401: dict, 403: dict, 404: dict},
)
def update_project(request, project_id: uuid.UUID, payload: ProjectIn):
    """Update project. Requires auth; must own."""
    if not request.user.is_authenticated:
        return 401, {"detail": "Authentication required"}
    try:
        obj = Project.objects.get(pk=project_id)
    except Project.DoesNotExist:
        return 404, {"detail": "Not found"}
    if obj.user_id != request.user.id:
        return 403, {"detail": "Forbidden"}
    obj.title = payload.title
    obj.description = payload.description
    obj.technologies = payload.technologies or []
    obj.url = payload.url
    obj.display_order = payload.display_order
    obj.save()
    return 200, obj


@router.delete(
    "profile/projects/{project_id}",
    response={204: None, 401: dict, 403: dict, 404: dict},
)
def delete_project(request, project_id: uuid.UUID):
    """Delete project. Requires auth; must own."""
    if not request.user.is_authenticated:
        return 401, {"detail": "Authentication required"}
    try:
        obj = Project.objects.get(pk=project_id)
    except Project.DoesNotExist:
        return 404, {"detail": "Not found"}
    if obj.user_id != request.user.id:
        return 403, {"detail": "Forbidden"}
    obj.delete()
    return 204, None
