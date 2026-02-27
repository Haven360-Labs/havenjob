**Based on:** PRD v1.3 + Database Schema (v2.1)  
**Date:** February 23, 2026

---

## Overview

HavenJob is **open-source** and self-hostable. A managed **cloud platform** (haven360labs) is also offered where users pay via **credits or subscriptions** for AI and email processing features.

Implementation is split into four sequential phases:

| Phase | Name | Deliverable |
|-------|------|-------------|
| 1 | Foundation & Auth | Running app with register/login/onboarding |
| 2 | Job Tracker | Full manual + email-forwarding job tracking |
| 3 | AI Career Assistant | Profile, CV upload, and AI chat |
| 4 | AI Tools | Cover letter, CV tailor, Q&A answerer |

---

## Project Structure

This is a **monorepo** with two top-level workspaces:

```
havenjob/
├── docs/                            ← PRD, schema, implementation plan
├── .env.example                     ← Root env vars shared across workspaces
│
├── backend/                         ← Django + django-ninja API
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env
│   │
│   ├── config/                      ← Django project settings
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   ├── development.py
│   │   │   └── production.py
│   │   ├── urls.py                  ← Mounts all ninja routers
│   │   └── wsgi.py
│   │
│   ├── apps/                        ← One Django app per domain
│   │   ├── users/                   ← Auth, profile, trusted senders, provider settings
│   │   │   ├── models.py
│   │   │   ├── api.py               ← django-ninja Router
│   │   │   ├── schemas.py           ← Pydantic input/output schemas
│   │   │   ├── services.py          ← Business logic (keep api.py thin)
│   │   │   └── migrations/
│   │   │
│   │   ├── tracker/                 ← Job applications, status history
│   │   │   ├── models.py
│   │   │   ├── api.py
│   │   │   ├── schemas.py
│   │   │   ├── services.py
│   │   │   └── migrations/
│   │   │
│   │   ├── notifications/           ← Notifications + preferences
│   │   │   ├── models.py
│   │   │   ├── api.py
│   │   │   ├── schemas.py
│   │   │   ├── services.py
│   │   │   └── migrations/
│   │   │
│   │   └── ai/                      ← Chat, CV, Q&A, ai_outputs, job_descriptions
│   │       ├── models.py
│   │       ├── api.py
│   │       ├── schemas.py
│   │       ├── services.py
│   │       └── migrations/
│   │
│   ├── providers/                   ← Plugin registries (no models, no migrations)
│   │   ├── email/
│   │   │   ├── base.py              ← EmailInboundProvider ABC + ParsedEmail
│   │   │   ├── gmail.py
│   │   │   ├── sendgrid.py
│   │   │   ├── registry.py          ← EMAIL_PROVIDER_REGISTRY dict
│   │   │   └── factory.py          ← get_email_provider_for_user()
│   │   │
│   │   └── llm/
│   │       ├── base.py              ← LLMProvider ABC
│   │       ├── openai.py
│   │       ├── anthropic.py
│   │       ├── registry.py          ← LLM_PROVIDER_REGISTRY dict
│   │       └── factory.py          ← get_llm_for_user()
│   │
│   └── core/                        ← Shared utilities (no models)
│       ├── auth.py                  ← Auth helpers for django-ninja
│       ├── billing.py               ← Credit check middleware (cloud mode only)
│       ├── storage.py               ← S3 upload helpers
│       ├── pagination.py
│       └── exceptions.py
│
└── frontend/                        ← Next.js App Router (TypeScript)
    ├── package.json
    ├── next.config.ts
    ├── tsconfig.json
    ├── .env.local                   ← NEXT_PUBLIC_API_URL etc.
    │
    ├── app/                         ← Next.js App Router pages
    │   ├── layout.tsx               ← Root layout (fonts, global styles)
    │   ├── page.tsx                 ← Landing / marketing page
    │   ├── (auth)/                  ← Route group: unauthenticated pages
    │   │   ├── login/page.tsx
    │   │   ├── register/page.tsx
    │   │   └── forgot-password/page.tsx
    │   ├── (app)/                   ← Route group: authenticated pages
    │   │   ├── layout.tsx           ← App shell (sidebar, header)
    │   │   ├── dashboard/page.tsx
    │   │   ├── onboarding/page.tsx
    │   │   ├── applications/
    │   │   │   ├── page.tsx         ← Applications list
    │   │   │   └── [id]/page.tsx    ← Application detail
    │   │   ├── profile/page.tsx
    │   │   ├── ai/
    │   │   │   ├── chat/page.tsx
    │   │   │   ├── cover-letter/page.tsx
    │   │   │   ├── tailor-cv/page.tsx
    │   │   │   └── interview/page.tsx
    │   │   └── settings/page.tsx
    │   └── api/                     ← Next.js API routes (proxy/auth only)
    │       └── auth/[...nextauth]/route.ts
    │
    ├── components/                  ← Reusable UI components
    │   ├── ui/                      ← Base primitives (Button, Input, Modal...)
    │   ├── layout/                  ← Sidebar, Header, AppShell
    │   ├── tracker/                 ← ApplicationCard, StatusBadge, StatusTimeline
    │   ├── ai/                      ← ChatPanel, MessageBubble, OutputCard
    │   └── shared/                  ← NotificationBell, ProviderSelector...
    │
    ├── lib/
    │   ├── api.ts                   ← Typed API client (fetch wrapper for Django backend)
    │   ├── auth.ts                  ← Auth helpers + token management
    │   └── utils.ts
    │
    └── types/                       ← Shared TypeScript types matching backend schemas
        └── index.ts
```

### Router mounting in `config/urls.py`

```python
from ninja import NinjaAPI
from apps.users.api import router as users_router
from apps.tracker.api import router as tracker_router
from apps.notifications.api import router as notifications_router
from apps.ai.api import router as ai_router

api = NinjaAPI(title="HavenJob API")
api.add_router("/users/",         users_router)
api.add_router("/tracker/",       tracker_router)
api.add_router("/notifications/", notifications_router)
api.add_router("/ai/",            ai_router)

urlpatterns = [path("api/", api.urls)]
```

### Convention: keep `api.py` thin

```python
# apps/tracker/api.py  ← only routing + schema wiring
@router.post("/", response=ApplicationOut, auth=JWTAuth())
def create_application(request, payload: ApplicationIn):
    return ApplicationService.create(user=request.user, data=payload)

# apps/tracker/services.py  ← all logic lives here
class ApplicationService:
    @staticmethod
    def create(user, data): ...
```

---

## Tech Stack Decisions (To Confirm)

| Layer | Decision | Notes |
|-------|----------|-------|
| **Backend** | Django + django-ninja | Confirmed |
| **Database** | PostgreSQL | Required for GIN, JSONB, partial UNIQUE |
| **ORM** | Django ORM | Built-in with Django |
| **File Storage** | AWS S3 | For CV uploads |
| **Email Inbound** | **Pluggable** — Gmail or SendGrid | User/admin configures per-instance |
| **LLM** | **Pluggable** — OpenAI or Anthropic | User selects in settings; abstraction layer handles routing |
| **Auth** | django-allauth | Supports Google/LinkedIn OAuth |
| **Hosting (Cloud)** | Railway or Render | For managed cloud platform |
| **Monetization** | Credits + Subscriptions (cloud only) | Self-hosted users bring their own API keys; cloud users pay via credits |

---

## Phase 1: Foundation & Authentication

**Goal:** Users can register, log in, and complete onboarding.

### 1.1 Project Setup
- [ ] Initialize Django project with django-ninja
- [ ] Configure PostgreSQL database connection (`settings.py`)
- [ ] Set up `django-environ` for environment variable management (`.env`)
- [ ] Configure Django migrations tooling
- [ ] Set up `pylint` / `ruff` for linting
- [ ] Initialize `django-allauth` and configure OAuth providers (Google, LinkedIn)
- [ ] Configure `django-storages` + `boto3` for AWS S3 file storage

### 1.2 Database Migrations – Auth + Settings Tables
- [ ] Create `users` table (all fields from schema)
- [ ] Create `trusted_senders` table with `UNIQUE(user_id, sender_email)`
- [ ] Create `user_notification_preferences` table
- [ ] Create `user_provider_settings` table _(new — see Provider Abstraction below)_

### 1.3 Authentication
- [ ] **Registration**: Email + password endpoint via django-ninja; hash with Django's built-in `make_password`; generate unique `forwarding_address` on registration
- [ ] **Login**: Session management (Django sessions or JWT via `djangorestframework-simplejwt`)
- [ ] **Social Auth**: Google OAuth integration via `django-allauth`
- [ ] **Password Recovery**: Forgot password → email reset link flow (Django's built-in password reset)
- [ ] **Auth Guards**: Protect all API routes using django-ninja's auth middleware

### 1.4 Onboarding Flow (UI)
- [ ] Step 1: Registration form (UI)
- [ ] Step 2: Display generated forwarding address prominently
- [ ] Step 3: Add first trusted sender (with suggestion chips for common ones)
- [ ] Step 4: Quick profile form (name, target role)
- [ ] Step 5: **Provider setup** — choose email provider (Gmail/SendGrid) and LLM provider (OpenAI/Anthropic), enter API key
- [ ] Step 6: Dashboard redirect with tooltip tour
- [ ] Skippable steps; `onboarding_completed` flag saved on finish

### 1.5 Settings Page
- [ ] Trusted Sender CRUD UI (add / label / remove)
- [ ] View forwarding address (copy-to-clipboard button)
- [ ] Notification preferences toggle (email / in-app)
- [ ] **Provider Settings panel**: Choose LLM provider + enter API key; choose email provider + configure

---

## Provider Abstraction Layer (Cross-Phase)

> Because both the LLM and email providers are user-configurable, both must be implemented behind a clean abstraction interface. This prevents tight coupling to any single provider.

### LLM Abstraction
- [ ] Create `LLMProvider` base class with a standard `chat(messages, context)` method
- [ ] `OpenAIProvider` implementation (GPT-4o)
- [ ] `AnthropicProvider` implementation (Claude)
- [ ] `get_llm_for_user(user_id)` factory function — reads user's stored provider + API key and returns the correct provider instance
- [ ] All AI endpoints call `get_llm_for_user()` — never hardcode a provider

### Email Inbound Abstraction (Registry + Factory + Strategy)

The email provider system combines three patterns deliberately:

- **Registry** — a dict maps provider name strings (as stored in the DB) to provider classes. This is the only place that needs to change when a new provider is added.
- **Factory** — `get_email_provider_for_user()` reads the user's configured provider from `user_provider_settings` and instantiates the correct class from the registry. No `if/elif` chains.
- **Strategy** — the returned provider object is the swappable behaviour used by all calling code.

**This is the exact pattern to implement:**

```python
# providers/email/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class ParsedEmail:
    """Shared output schema for all email providers."""
    company_name: str | None
    job_title: str | None
    sender_email: str
    received_at: datetime
    raw_subject: str
    confidence_score: float  # 0.0 – 1.0

class EmailInboundProvider(ABC):
    @abstractmethod
    def setup(self, user) -> None:
        """Configure / authorise the provider for a user."""

    @abstractmethod
    def parse_inbound(self, payload: dict) -> ParsedEmail:
        """Extract structured data from the inbound webhook payload."""

    @abstractmethod
    def get_webhook_url(self) -> str:
        """Return the webhook path this provider listens on."""


# providers/email/gmail.py
class GmailProvider(EmailInboundProvider):
    """Per-user OAuth. Free / self-hosted tier."""
    def setup(self, user): ...
    def parse_inbound(self, payload) -> ParsedEmail: ...
    def get_webhook_url(self) -> str: return "/webhooks/email/gmail"


# providers/email/sendgrid.py
class SendGridProvider(EmailInboundProvider):
    """Inbound Parse webhook. Cloud / paid tier."""
    def setup(self, user): ...
    def parse_inbound(self, payload) -> ParsedEmail: ...
    def get_webhook_url(self) -> str: return "/webhooks/email/sendgrid"


# providers/email/registry.py  ← ONLY file to edit when adding a new provider
from .gmail import GmailProvider
from .sendgrid import SendGridProvider

EMAIL_PROVIDER_REGISTRY: dict[str, type[EmailInboundProvider]] = {
    "gmail":    GmailProvider,
    "sendgrid": SendGridProvider,
    # "outlook": OutlookProvider,  ← add new providers here only
}


# providers/email/factory.py
def get_email_provider_for_user(user_id: UUID) -> EmailInboundProvider:
    """Factory: reads user setting from DB, returns correct provider instance."""
    settings = UserProviderSettings.objects.get(user_id=user_id, provider_type="email_inbound")
    provider_class = EMAIL_PROVIDER_REGISTRY[settings.provider_name]
    return provider_class()


# Usage in any API endpoint or service:
provider = get_email_provider_for_user(user.id)   # Strategy
parsed   = provider.parse_inbound(webhook_payload)
```

> **To add a new email provider:** create a new file in `providers/email/`, implement `EmailInboundProvider`, and add one entry to `EMAIL_PROVIDER_REGISTRY`. No other files change.

**Implementation checklist:**
- [ ] Create `providers/email/base.py` — `EmailInboundProvider` ABC + `ParsedEmail` dataclass
- [ ] Create `providers/email/gmail.py` — `GmailProvider` (per-user OAuth, Pub/Sub webhook)
- [ ] Create `providers/email/sendgrid.py` — `SendGridProvider` (Inbound Parse webhook)
- [ ] Create `providers/email/registry.py` — `EMAIL_PROVIDER_REGISTRY` dict
- [ ] Create `providers/email/factory.py` — `get_email_provider_for_user()` factory
- [ ] Webhook router endpoint dispatches to `provider.parse_inbound(payload)`

### New Schema Table: `user_provider_settings`
```
Column              Type                              Notes
---                 ---                               ---
id                  UUID PK
user_id             UUID FK → users.id
provider_type       Enum(llm, email_inbound)
provider_name       Enum(openai, anthropic, gmail, sendgrid)
encrypted_api_key   String Nullable                   Encrypted at rest
created_at          Timestamp
updated_at          Timestamp
```
- `UNIQUE(user_id, provider_type)` — one active provider per type per user
- API keys stored encrypted (e.g., using Django's `cryptography` library or AWS KMS)

---

## Phase 2: Job Tracker

**Goal:** Users can manually add applications and auto-log them via email forwarding.

### 2.1 Database Migrations – Tracker Tables
- [ ] Create `applications` table (with all indexes and constraints)
- [ ] Create `application_status_history` table
- [ ] Create `notifications` table

### 2.2 Manual Application CRUD
- [ ] `POST /applications` – create application
- [ ] `GET /applications` – list user's applications (with filtering/sorting)
- [ ] `PATCH /applications/:id` – update fields or status
- [ ] `DELETE /applications/:id` – soft-delete (set `deleted_at`)
- [ ] On status change: write record to `application_status_history` with `changed_by = 'user'`

### 2.3 Dashboard UI
- [ ] Main dashboard layout shell (sidebar nav, header)
- [ ] Application list/table view with columns: Company, Title, Date Applied, Status, Source
- [ ] Status badge component (colour-coded per status)
- [ ] Sorting (by date, status) and filtering (by status, date range, source)
- [ ] Full-text search bar (maps to GIN index on company_name + job_title)
- [ ] "Add Application" button → modal form

### 2.4 Application Detail View
- [ ] Inline editable fields (company, title, notes, etc.)
- [ ] Status timeline (from `application_status_history`)
- [ ] Archive / delete actions

### 2.5 Email Forwarding Pipeline
- [ ] Configure inbound email provider (SendGrid Inbound Parse / Postmark)
- [ ] `POST /webhooks/email-inbound` endpoint
- [ ] Verify sender email against user's `trusted_senders` (match on forwarding address in To field)
- [ ] If untrusted sender → silently discard
- [ ] Extract: company name, job title, date (regex + LLM fallback)
- [ ] Compute `raw_email_hash` for deduplication check
- [ ] Create `application` record with `source = 'email'`, `changed_by = 'email_parser'`
- [ ] Flag `is_needs_review = true` if confidence_score < threshold
- [ ] Create in-app `notification` record

### 2.6 Notification System (Basic)
- [ ] Notification bell in header (unread count badge)
- [ ] Notification dropdown list
- [ ] Mark as read on open

---

## Phase 3: AI Career Assistant – Profile & Chat

**Goal:** Users can build a profile and have grounded AI conversations.

### 3.1 Database Migrations – AI Profile Tables
- [ ] Create `education` table
- [ ] Create `work_experiences` table
- [ ] Create `projects` table
- [ ] Create `cv_documents` table (with `UNIQUE(user_id) WHERE is_primary = true`)
- [ ] Create `chat_sessions` table
- [ ] Create `chat_messages` table

### 3.2 Profile Management
- [ ] Profile page layout with sections: Personal Info, Work Experience, Projects, Education, Skills
- [ ] CRUD forms for each section (add / edit / delete / reorder via `display_order`)
- [ ] Profile completeness percentage calculation (update `users.profile_completion_percent`)
- [ ] Progress bar / checklist in UI nudging users to complete profile

### 3.3 CV Upload
- [ ] `POST /cv/upload` – accept PDF or DOCX, validate size/type
- [ ] Upload to S3 / R2, store `file_url` and `file_name` in `cv_documents`
- [ ] Extract text from PDF (using `pdf-parse` / `pdfplumber` / similar)
- [ ] Store `parsed_text` in `cv_documents`
- [ ] Set as `is_primary = true` (unset previous primary via transaction)
- [ ] Parse and pre-fill profile sections from extracted text (optional AI step)

### 3.4 LLM Service Layer
- [ ] Create a centralised `LLMService` class / module
- [ ] Configure LLM provider (OpenAI / Anthropic)
- [ ] `buildContext(userId)` function: assembles profile data (work experience, projects, education, skills, CV text) into system prompt context
- [ ] Rate limiting and error handling
- [ ] Streaming support for chat responses

### 3.5 AI Chat
- [ ] `POST /chat/sessions` – create new session
- [ ] `POST /chat/sessions/:id/messages` – send message; retrieve profile context; call LLM; stream response
- [ ] Save messages to `chat_messages` (both `user` and `assistant` roles)
- [ ] Auto-generate session title from first message
- [ ] Chat UI: floating button or sidebar panel
- [ ] Message history display per session
- [ ] Copy-to-clipboard button per AI response
- [ ] Session list sidebar (past conversations)

---

## Phase 4: AI Tools – Cover Letter, CV Tailor, Q&A

**Goal:** Users can generate documents and answers grounded in their profile.

### 4.1 Database Migrations – AI Tools Tables
- [ ] Create `job_descriptions` table (with UNIQUE constraint on `content_hash`)
- [ ] Create `interview_questions` table (seed with library of common questions)
- [ ] Create `user_answers` table
- [ ] Create `ai_outputs` table

### 4.2 Job Description Store
- [ ] `POST /job-descriptions` – accept raw JD text; compute `content_hash`; deduplicate per user
- [ ] Link to `application_id` if provided
- [ ] Reuse existing `job_description_id` if hash matches

### 4.3 Cover Letter Generator
- [ ] Dedicated "Cover Letter" page
- [ ] User pastes JD → saves to `job_descriptions`
- [ ] Tone selector (Formal / Conversational / Enthusiastic)
- [ ] `POST /ai/cover-letter` → call LLM with profile context + JD + tone → return cover letter
- [ ] Store result in `ai_outputs` (type: `cover_letter`)
- [ ] Inline editable output
- [ ] Download as `.docx` + copy to clipboard

### 4.4 CV Tailor
- [ ] Dedicated "Tailor CV" page
- [ ] User pastes JD → saves to `job_descriptions`
- [ ] `POST /ai/tailor-cv` → LLM compares profile against JD → returns section-by-section suggestions + tailored summary
- [ ] Store result in `ai_outputs` (type: `tailored_cv`)
- [ ] Side-by-side view: original vs. suggested
- [ ] Accept/reject suggestions per section
- [ ] Download tailored CV as `.docx` or `.pdf`

### 4.5 Interview Q&A Bank
- [ ] Seed DB with pre-loaded `interview_questions` (behavioural + standard categories)
- [ ] Q&A page: browse questions by category and type
- [ ] User can write draft answer per question
- [ ] `POST /ai/improve-answer` → send draft to LLM → return STAR-structured suggestion
- [ ] Store improved answer in `user_answers.ai_improved_answer`
- [ ] Accept/reject improvement UI
- [ ] Add custom question flow

### 4.6 Application Question Answerer
- [ ] "Answer Questions" page (or accessible via AI chat)
- [ ] User pastes one or more application form questions
- [ ] `POST /ai/answer-questions` → LLM generates contextual answer per question using profile + Q&A bank
- [ ] Store each result in `ai_outputs` (type: `question_answer`)
- [ ] Per-answer: copy, regenerate, add context
- [ ] Support multi-question batch input

---

## Cross-Cutting Concerns

### Security
- [ ] All endpoints require authenticated session
- [ ] Input validation and sanitisation on all forms and API endpoints
- [ ] CV file type validation (reject non-PDF/DOCX)
- [ ] Rate limiting on AI endpoints to control LLM costs
- [ ] No raw email body stored beyond parsed fields (`parse_metadata` JSONB only)
- [ ] CV stored encrypted at rest (via S3 server-side encryption)

### Error Handling
- [ ] Global error handler returning consistent JSON error shape
- [ ] AI endpoint fallbacks (retry on timeout, friendly error message)
- [ ] Email parser failure → create `is_needs_review = true` application, notify user

### Soft Deletes
- [ ] All critical tables with `deleted_at` excluded from default queries using scoped queries/middleware
- [ ] Admin-level purge endpoint for GDPR right-to-erasure

---

## Dependency Order (Schema → Backend → UI)

```
Phase 1: users → trusted_senders → user_notification_preferences
            ↓
Phase 2: applications → application_status_history → notifications
            ↓
Phase 3: education, work_experiences, projects, cv_documents → chat_sessions → chat_messages
            ↓
Phase 4: job_descriptions → interview_questions → user_answers → ai_outputs
```

Each table must be created (migrated) before the API layer is built, and the API layer before the UI.

---

## Monetization Model (Cloud Platform)

The open-source project is self-hostable with **no restrictions** — users bring their own API keys. The managed **HavenJob Cloud** platform charges as follows:

| Tier | Model | Includes |
|------|-------|----------|
| **Free / Self-Hosted** | No cost | Full app, bring-your-own API keys |
| **Cloud – Credits** | Pay-per-use | Users purchase credits; AI calls and email parsing deduct credits |
| **Cloud – Subscription** | Monthly/Annual | Flat fee for a generous usage allowance |

**Implementation tasks:**
- [ ] Add `credits_balance` and `subscription_tier` to `users` table
- [ ] Middleware: on each AI/email API call, check balance and deduct credits (cloud only)
- [ ] Billing API: integrate Stripe for subscription and credit top-up purchases
- [ ] Self-hosted mode: skip credit check entirely (env flag: `CLOUD_MODE=false`)

---

## Open Questions Remaining

| # | Question | Impact |
|---|----------|--------|
| 1 | Railway or Render for cloud hosting? | Affects deployment config |
| 2 | Credit pricing model — cost per AI call, or bundled? | Affects billing middleware |
