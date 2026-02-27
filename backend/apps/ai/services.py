"""AI app business logic and service layer."""

from django.contrib.auth import get_user_model

from providers.llm.base import LLMProvider
from providers.llm.factory import get_llm


def build_context(user) -> str:
    """
    Build system-prompt context from user profile (work experience, projects, education, CV).
    Used to ground the AI career assistant.
    """
    User = get_user_model()
    if not isinstance(user, User):
        user = User.objects.get(pk=user)
    parts = ["You are a helpful career assistant. Use the following profile context when relevant.\n"]
    if user.full_name:
        parts.append(f"Name: {user.full_name}")
    if user.target_role:
        parts.append(f"Target role: {user.target_role}")
    if user.skills:
        skills = user.skills if isinstance(user.skills, list) else user.skills.values() if isinstance(user.skills, dict) else []
        if skills:
            parts.append(f"Skills: {', '.join(str(s) for s in skills)}")
    work = getattr(user, "work_experiences", None)
    if work is not None and hasattr(work, "all"):
        for w in work.all()[:20]:
            parts.append(f"Experience: {w.role} at {w.company} ({w.start_date} - {w.end_date or 'present'}). {w.description or ''}")
    projs = getattr(user, "projects", None)
    if projs is not None and hasattr(projs, "all"):
        for p in projs.all()[:20]:
            parts.append(f"Project: {p.title}. {p.description}")
    edu = getattr(user, "education", None)
    if edu is not None and hasattr(edu, "all"):
        for e in edu.all()[:20]:
            parts.append(f"Education: {e.degree} at {e.institution} ({e.field_of_study or ''})")
    cv = getattr(user, "cv_documents", None)
    if cv is not None and hasattr(cv, "filter"):
        primary = cv.filter(is_primary=True).first()
        if primary and primary.parsed_text:
            parts.append("--- CV / Resume (extracted text) ---")
            parts.append(primary.parsed_text[:8000] or "")
    return "\n\n".join(parts)


COVER_LETTER_TONE_INSTRUCTIONS = {
    "formal": "Use a formal, professional tone. Avoid casual language and contractions.",
    "conversational": "Use a warm, conversational tone while remaining professional.",
    "enthusiastic": "Use an enthusiastic, confident tone that shows strong interest in the role.",
}


def build_cover_letter_system_prompt(
    profile_context: str,
    job_description: str,
    tone: str = "formal",
) -> str:
    """
    Build the system prompt for cover letter generation.

    Combines profile context (candidate info) with the job description and
    tone instructions so the LLM can generate a tailored cover letter.
    """
    tone_instruction = COVER_LETTER_TONE_INSTRUCTIONS.get(
        tone.lower(), COVER_LETTER_TONE_INSTRUCTIONS["formal"]
    )
    return f"""You are an expert at writing job application cover letters.

{tone_instruction}

Use the following candidate profile to tailor the letter. Do not invent facts; only use information from the profile.

--- CANDIDATE PROFILE ---
{profile_context}

--- JOB DESCRIPTION ---
{job_description}

--- INSTRUCTIONS ---
Write a cover letter that:
1. Addresses the hiring manager (use "Dear Hiring Manager" if no name is given).
2. Opens with a strong hook that ties the candidate's background to the role.
3. Highlights 2-3 relevant achievements or skills from the profile that match the JD.
4. Shows genuine interest in the company and role.
5. Closes with a clear call to action and professional sign-off.
6. Stays within one page when formatted (roughly 250-400 words).
Output only the cover letter text, no meta-commentary."""


def build_improve_answer_system_prompt(question: str | None) -> str:
    """
    Build the system prompt for improving a draft interview answer into STAR format.

    STAR = Situation, Task, Action, Result. Used for behavioural interview answers.
    """
    q_context = f"\nThe question to answer: {question}" if (question and question.strip()) else ""
    return f"""You are an expert interview coach. Rewrite the user's draft answer into a clear STAR-format response.

STAR format:
- **Situation**: Brief context (1-2 sentences).
- **Task**: Your responsibility or goal.
- **Action**: What you did (concrete steps, 2-4 sentences).
- **Result**: Outcome, metrics, or learning (1-2 sentences).
{q_context}

Instructions:
1. Keep the user's core story and facts; improve clarity and structure.
2. Use first person and past tense where appropriate.
3. Be concise: aim for 150-250 words total unless the question needs more.
4. Output only the improved answer text, no labels like "Situation:" (optional subheadings are fine).
5. Do not add meta-commentary or "Here is your improved answer"."""


class LLMService:
    """
    Service to communicate with the configured LLM (OpenAI or Anthropic).

    Configure via env: LLM_PROVIDER=openai|anthropic, OPENAI_API_KEY or ANTHROPIC_API_KEY.
    """

    def __init__(self, provider: str | None = None, llm: LLMProvider | None = None):
        self._llm = llm if llm is not None else get_llm(provider)

    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        system_prompt: str | None = None,
        max_tokens: int = 2048,
    ) -> str:
        """Send messages to the LLM and return the assistant reply text."""
        return self._llm.complete(
            messages,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
        )

    def stream_complete(
        self,
        messages: list[dict[str, str]],
        *,
        system_prompt: str | None = None,
        max_tokens: int = 2048,
    ):
        """Send messages to the LLM and stream the assistant reply as text chunks."""
        return self._llm.stream_complete(
            messages,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
        )
