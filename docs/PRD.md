# HavenJob – Product Requirements Document (PRD)

**Version:** 1.3  
**Date:** February 20, 2026  
**Status:** Draft  

---

## 1. Overview

### 1.1 Product Summary

**HavenJob** is a job application tracking platform that helps job seekers stay organized and succeed throughout their job search. Users can track every application they send and leverage an AI Career Assistant — powered by their personal profile, CV, and project history — to draft cover letters, tailor CVs, answer job application questions, and prepare behavioural interview responses.

### 1.2 Problem Statement

Job seekers often apply to dozens (or hundreds) of positions, making it difficult to:
- Remember which companies they applied to and on what date.
- Know the current status of each application.
- Follow up at the right time.
- Keep a centralized, up-to-date record of their job search activity.
- Write tailored, high-quality cover letters and application answers for every role.
- Prepare compelling behavioural interview responses quickly.

### 1.3 Goals

| Goal | Success Metric |
|------|----------------|
| Give users a single source of truth for all job applications | 80% of active users have ≥5 applications logged within their first 7 days |
| Reduce manual data-entry friction via email forwarding | ≥40% of applications logged via email forwarding within 60 days of launch |
| Help users track application status end-to-end | Average application has at least 2 status updates before closure |
| Enable AI-assisted job application writing | ≥50% of active users use AI features at least once per week |

---

## 2. Target Users

### Primary Persona: The Active Job Seeker
- Applying to 10–50 jobs per month.
- Uses Gmail, Outlook, or similar email clients.
- Wants a lightweight way to stay organized without building their own spreadsheet.

### Secondary Persona: The Passive Job Seeker
- Exploring opportunities but not aggressively applying.
- May apply to a few roles per month.
- Values simplicity and low-friction tracking.

---

## 3. Feature Releases

This PRD covers two feature releases:
- **Core Infrastructure:** Authentication & Onboarding
- **Feature 1 (MVP):** Job Tracker
- **Feature 2:** AI Career Assistant

---

## 4. Core Infrastructure: Authentication & Onboarding

### 4.1 Authentication

**User Story:** As a job seeker, I want to create a secure account so that my CV, projects, and application history are protected and accessible only to me.

**Acceptance Criteria:**
- **Registration**: User can sign up using Email/Password.
- **Social Auth**: Support for "Sign in with Google" and "Sign in with LinkedIn" for lower friction.
- **Login**: Secure login for existing users.
- **Password Recovery**: "Forgot Password" flow via email.
- **Security**: Mandatory HTTPS; passwords hashed and salted; session management (remember me).

### 4.2 Onboarding Flow

**User Story:** As a new user, I want a guided setup so I immediately understand how to use the email forwarding and AI features.

**The Onboarding Journey:**
1. **Account Creation**: (See 4.1).
2. **Forwarding Setup**: System generates the user's unique `@havenjob.app` address and displays it prominently.
3. **Trusted Senders**: Prompt user to add their first trusted sender (e.g., their own Gmail or `no-reply@linkedin.com`).
4. **Initial Profile**: Quick-start form for name, target role, and optional CV upload (to seed the AI Assistant).
5. **Dashboard Tour**: High-level tooltip tour of the Job Tracker and AI Chat features.

**Acceptance Criteria:**
- Unique forwarding email is generated immediately upon registration.
- Users can skip secondary onboarding steps to reach the dashboard quickly.
- Progress bar or checklist showing onboarding completion.

---

## 5. Feature 1: Job Tracker

### Feature Requirements

### 4.1 Adding Job Applications

Users need two ways to add applications to their tracker.

#### 4.1.1 Manual Entry

**User Story:** As a job seeker, I want to manually log a job application so that I can track it even if I didn't receive a confirmation email.

**Acceptance Criteria:**
- User can click **"Add Application"** and fill in a form.
- Required fields: **Company Name**, **Job Title**, **Date Applied**.
- Optional fields: **Job URL**, **Location**, **Salary Range**, **Notes**, **Application Source** (e.g., LinkedIn, Company Website, Referral).
- After submission, the application appears immediately in the application list.

---

#### 4.1.2 Email Forwarding

**User Story:** As a job seeker, I want to forward my job application confirmation emails to HavenJob so that my applications are automatically logged without manual data entry.

**System Flow:**

```
User forwards email → HavenJob inbox → Parser extracts job details → 
Application created in user's account → User notified
```

**Feature Details:**

- Each user is assigned a **unique forwarding email address** (e.g., `track+<user-id>@havenjob.app`).
- The user configures a list of **trusted sender emails** in their settings — only emails from these senders are processed (to prevent spam or accidental logging).
- HavenJob parses the forwarded email and extracts:
  - Company name
  - Job title (if identifiable)
  - Date applied (from email timestamp)
  - Original sender / source
- A new application is created with status **"Applied"** automatically.
- The user receives an **in-app notification** (and optional email) confirming the application was logged.
- If parsing fails or confidence is low, the application is flagged for **manual review** by the user.

**Acceptance Criteria:**
- User can view their unique forwarding email address in Account Settings.
- User can add, edit, and remove trusted sender emails.
- Applications forwarded from trusted senders are created automatically.
- Emails from non-trusted senders are silently ignored with no application created.
- Parsed but uncertain fields are surfaced to the user for confirmation.

---

### 4.2 Application Status Tracking

**User Story:** As a job seeker, I want to track the current status of each application so I know where I stand with every company.

#### 4.2.1 Status Workflow

Applications move through the following statuses:

```
Applied → Under Review → Phone Screen → Interview → Offer → Accepted
                                                          ↘ Rejected
                ↘ Rejected / Withdrawn (at any stage)
```

| Status | Description |
|--------|-------------|
| **Applied** | Application submitted; awaiting response. |
| **Under Review** | Employer has acknowledged receipt and is reviewing. |
| **Phone Screen** | Initial screen scheduled or completed. |
| **Interview** | One or more interviews scheduled or completed. |
| **Offer** | A job offer has been extended. |
| **Accepted** | User has accepted the offer. |
| **Rejected** | Application was declined by the employer. |
| **Withdrawn** | User withdrew their application. |

**Acceptance Criteria:**
- User can update the status of any application at any time.
- Status changes are recorded with a timestamp and displayed in a **timeline/history view** per application.
- The application list view shows the current status for each entry with a visual status badge.

---

### 4.3 Application List & Dashboard

**User Story:** As a job seeker, I want to see all my applications in one place, with the ability to filter and sort them.

**Acceptance Criteria:**
- Applications are displayed in a sortable list/table (default: most recent first).
- User can **filter** by: Status, Date Range, Application Source.
- User can **search** by Company Name or Job Title.
- Each row shows: Company, Job Title, Date Applied, Status, Source.
- Clicking a row opens the **Application Detail View**.

#### 4.3.1 Application Detail View

- All fields entered at creation (editable).
- Current status (editable).
- Status history / timeline.
- Notes section (free text, editable).
- Option to **Archive** or **Delete** the application.

---

### 4.4 Account & Email Settings

**User Story:** As a user, I want to manage my trusted sender emails so that only relevant confirmation emails create applications in my tracker.

**Acceptance Criteria:**
- User can view their unique forwarding email address.
- User can add one or more trusted sender email addresses (e.g., `no-reply@linkedin.com`, `jobs@greenhouse.io`).
- Trusted senders are validated as proper email format.
- User can remove any trusted sender at any time.
- A helper section shows **common known job board sender emails** users may want to add (e.g., LinkedIn, Greenhouse, Lever, Workday).

---

## 6. Feature 2: AI Career Assistant

### 5.1 Overview

The AI Career Assistant is a chat-based AI interface grounded in the user's personal profile. It uses the user's uploaded CV, project history, work experience, and a curated bank of behavioural Q&A to generate highly personalised responses — from cover letters to application form answers.

---

### 5.2 User Profile & Knowledge Base

**User Story:** As a job seeker, I want to build a personal profile so the AI can give me personalised, accurate assistance.

The **profile** is the AI's ground truth. It includes:

| Section | Details |
|---------|----------|
| **Personal Info** | Name, location, target roles, years of experience |
| **CV Upload** | PDF/DOCX upload; AI parses and indexes content |
| **Work Experience** | Companies, roles, dates, responsibilities (editable) |
| **Projects** | Project name, description, technologies used, outcomes |
| **Skills** | Technical and soft skills |
| **Education** | Degrees, certifications, institutions |
| **Behavioural Q&A Bank** | Common behavioural questions + user's drafted answers |

**Acceptance Criteria:**
- User can upload their CV (PDF or DOCX); parsed content is displayed for review and editing.
- User can manually add, edit, and delete entries in each profile section.
- Changes to the profile are immediately reflected in future AI responses.
- Profile completeness indicator nudges users to fill in missing sections.

---

### 5.3 Behavioural Q&A Bank

**User Story:** As a job seeker, I want to maintain a bank of behavioural questions and answers that the AI can improve and use when answering interview or application questions.

**Feature Details:**
- The system comes pre-loaded with a library of **common behavioural questions** (e.g., "Tell me about a time you handled conflict", "Describe a challenging project").
- Users can write their own draft answers to each question.
- The AI reviews and **suggests improvements** to answers — better structure (STAR format), stronger language, tighter storytelling.
- Users can accept, edit, or reject AI suggestions.
- Users can add custom questions not in the default library.

**Acceptance Criteria:**
- Pre-loaded question library is visible and browsable.
- User can write and save answers per question.
- AI improvement suggestions are displayed inline, with accept/reject controls.
- Accepted suggestions update the stored answer.

---

### 5.4 AI Chat Interface

**User Story:** As a job seeker, I want to chat with an AI assistant that knows my background so I can get instant, personalised answers.

**Feature Details:**
- A persistent chat interface accessible from any page.
- The AI has full context of the user's profile, CV, projects, and behavioural Q&A bank.
- The AI can answer open-ended questions like:
  - *"What should I say if asked about my biggest weakness?"*
  - *"Summarise my experience for a backend engineering role."*
  - *"What projects are most relevant for a fintech company?"*
- Chat history is saved per session.

**Acceptance Criteria:**
- Chat interface is accessible from a fixed position (e.g. sidebar or floating button).
- AI responses are grounded in the user's profile data, not generic advice.
- Users can copy any AI response to clipboard in one click.
- Chat sessions are persisted and can be revisited.

---

### 5.5 Cover Letter Generator

**User Story:** As a job seeker, I want to generate a tailored cover letter for a specific job so I can apply faster without sacrificing quality.

**Feature Details:**
- User pastes or types a **job description**.
- AI generates a cover letter using the user's profile, matching relevant experience and tone to the role.
- User can specify tone preferences (formal, conversational, enthusiastic).
- Output is editable inline before copying or downloading.

**Acceptance Criteria:**
- Cover letter generation triggered from a dedicated page or from the AI chat.
- Generated letter references specific user experience and aligns to job requirements.
- User can regenerate with a different tone or specific instructions.
- User can download as `.docx` or copy to clipboard.

---

### 5.6 CV Tailor

**User Story:** As a job seeker, I want to tailor my CV to a specific job description so I can improve my chances of passing ATS screening.

**Feature Details:**
- User pastes a **job description**.
- AI analyses it against the user's profile and suggests:
  - Which sections/bullet points to prioritise or reword.
  - Missing keywords the user should add (if the experience supports it).
  - A tailored CV summary/objective for that specific role.
- User can accept suggestions section by section.
- Final tailored CV can be downloaded as `.docx` or `.pdf`.

**Acceptance Criteria:**
- CV tailoring is accessible from a dedicated page or from the AI chat.
- AI highlights gaps between the job description and user profile.
- Suggestions are shown alongside the original content for easy comparison.
- Download of tailored CV is supported in at least one format (DOCX or PDF).

---

### 5.7 Job Application Question Answerer

**User Story:** As a job seeker, I want to paste application form questions and get AI-generated answers based on my profile so I can fill forms faster.

**Feature Details:**
- User pastes one or more application form questions (e.g., from a job portal form).
- AI generates answers grounded in the user's experience, projects, and behavioural Q&A bank.
- Each answer can be individually edited, regenerated, or copy-pasted.
- The AI adapts length and tone based on the nature of the question (short-form vs. essay).

**Acceptance Criteria:**
- User can paste multiple questions at once.
- AI generates a separate, contextually appropriate answer for each question.
- One-click copy per answer.
- User can provide additional context per question to refine the answer.

---

### 6.8 Out of Scope (Feature 2)

- Real-time interview simulation / mock interview audio.
- LinkedIn profile optimisation.
- Automatic job application submission.
- AI sourcing or job recommendations.

---

## 7. Quality Gates

These checks must pass for every user story before it is considered complete.

**Backend (Django — run from `backend/`):**
- `ruff check .` — Python linting
- `python manage.py test` — run the Django test suite

**Frontend (Next.js — run from `frontend/`):**
- `npm run lint` — ESLint checks
- `npx tsc --noEmit` — TypeScript type checking

**For UI-specific stories, also include:**
- Verify visual layout and responsiveness in the browser.

---

## 8. Out of Scope (Overall)

The following are **not** in scope across either release:

- Contact tracking (hiring managers, recruiters).
- Calendar integration for interview scheduling.
- Chrome extension for one-click job saving.
- Team/collaborative tracking.
- Mobile native apps (iOS / Android).

---

## 9. Non-Functional Requirements

| Category | Requirement |
|----------|-------------|
| **Performance** | Application list loads in <2s for up to 500 entries. AI responses return within 5s for standard queries. |
| **Security** | Forwarding emails processed in isolated queue; no raw email content stored beyond parsed fields. CV data stored encrypted at rest. |
| **Privacy** | Users can delete all profile data including uploaded CVs at any time. AI processing does not use personal data for model training. |
| **Reliability** | Email parsing service SLA of 99.5% uptime. AI service SLA of 99% uptime. |
| **Scalability** | System should support up to 10,000 users and 1M applications in phase 1 infrastructure. |
| **AI Quality** | AI responses must be grounded in user profile data; no speculative or fabricated experience claims. |

---

## 10. Technical User Stories (Beads)

The following stories are broken down into small, technically actionable beads for implementation.

### Epic: Authentication & Onboarding
| Task ID | Title | Description / Acceptance Criteria |
|---------|-------|-----------------------------------|
| AUTH-01 | Create User Database Schema | Add `users` table with auth fields (email, hashed_password) and profile fields (name, target_role). |
| AUTH-02 | Implement Registration API | Create endpoint for email/password registration. Must hash passwords safely. |
| AUTH-03 | Implement Registration UI | Build signup page with email, password, and validation errors. |
| AUTH-04 | Implement Login API & Session | Create login endpoint and session management (JWT or cookies). |
| AUTH-05 | Implement Login UI | Build login page with success redirect to dashboard. |
| ONB-01 | Generate Forwarding Address Logic | Add business logic to generate a unique `@havenjob.app` alias upon user registration. |
| ONB-02 | Trusted Sender Database Schema | Add `trusted_senders` table linked to `users`. |
| ONB-03 | Onboarding Flow UI | Build 3-step wizard: Show forwarding email -> Add Trusted Sender -> Quick Profile form. |

### Epic: Job Tracker Core
| Task ID | Title | Description / Acceptance Criteria |
|---------|-------|-----------------------------------|
| TRK-01 | Create Applications Schema | Add `applications` table (company, title, date, status, source, notes, user_id). |
| TRK-02 | Add Application API | Create POST endpoint to manually add a new job application. |
| TRK-03 | Applications List DB Query | Create efficient query to fetch a user's applications, sorted by date. |
| TRK-04 | Dashboard UI Shell | Build the main dashboard layout with navigation sidebar/header. |
| TRK-05 | Applications List UI | Build the data table/list view showing applications. |
| TRK-06 | Add Application Modal UI | Build the form modal to manually add an application. |
| TRK-07 | Status Update API | Create PATCH endpoint to update application status and log history. |
| TRK-08 | Status Badge & Dropdown UI | Add interactive status badge to list view allowing quick status changes. |
| TRK-09 | Application Detail View UI | Build expanded view showing full application details and notes. |

### Epic: Email Parsing & Automation
| Task ID | Title | Description / Acceptance Criteria |
|---------|-------|-----------------------------------|
| EML-01 | Email Webhook Endpoint Shell | Set up endpoint to receive incoming parsed emails from email provider (e.g., SendGrid/Postmark). |
| EML-02 | Sender Verification Logic | Add logic to webhook to verify sender against user's `trusted_senders` list. Drop if unverified. |
| EML-03 | Basic Email Extraction Logic | Extract company name, job title, and date from email body/subject using basic regex or LLM call. |
| EML-04 | Auto-Create Application Action | Wire extracted data to create a new application record with "Applied" status. |
| EML-05 | In-App Notification Schema | Add `notifications` table for system alerts. |
| EML-06 | Notification Trigger | Trigger notification when an application is auto-created. |

### Epic: AI Career Assistant
| Task ID | Title | Description / Acceptance Criteria |
|---------|-------|-----------------------------------|
| AI-01 | Profile Work History Schema | Add tables for user work experience, projects, and education. |
| AI-02 | Profile UI Form | Build pages for user to manage their work history and projects. |
| AI-03 | CV Upload API | Create endpoint to handle PDF/DOCX file upload and storage (e.g., S3). |
| AI-04 | CV File Parsing | Integrate library to extract raw text from uploaded PDFs. |
| AI-05 | Chat Session Schema | Create tables for `chat_sessions` and `chat_messages`. |
| AI-06 | LLM Integration Service | Set up service class to communicate with chosen LLM (OpenAI/Anthropic). |
| AI-07 | Chat API Endpoint | Create endpoint that takes user message, retrieves profile context, and streams LLM response. |
| AI-08 | Chat UI Component | Build the sliding/floating chat interface with message history. |
| AI-09 | Cover Letter Gen Prompt Engineering | Create specific system prompt for cover letters using profile context + provided JD. |
| AI-10 | Cover Letter UI View | Build the dedicated page/modal to paste JD and view/generate cover letter. |
| AI-11 | Behavioural Q&A Schema | Add table for `behavioural_questions` and user `answers`. |
| AI-12 | Q&A Improvement API | Create endpoint that sends user answer to LLM to return STAR-formatted improvements. |

---

## 11. Open Questions

**Feature 1 – Job Tracker**
1. **Email Parser Accuracy:** What confidence threshold triggers a "needs review" flag vs. auto-creating the application?
2. **Duplicate Detection:** If the same confirmation email is forwarded twice, how should the system handle it?
3. **Supported Email Clients:** Should the MVP support Gmail auto-forwarding rules, or only manual forwards?
4. **Notification Preferences:** Should users be able to opt out of email/in-app notifications for auto-logged applications?

**Feature 2 – AI Career Assistant**
5. **AI Model:** Which LLM provider will power the assistant (OpenAI, Anthropic, Gemini)? Will there be a fallback?
6. **CV Parsing Quality:** How will the system handle poorly formatted or image-based PDFs?
7. **Answer Accuracy Guardrails:** How do we prevent the AI from fabricating experience the user doesn't have?
8. **Data Retention:** How long is CV and profile data retained? Is there a right-to-erasure flow?
9. **Onboarding:** Should new users complete a profile setup wizard before accessing AI features?
10. **Free vs. Paid Tier:** Will AI features be gated behind a paid subscription? If so, what are the usage limits?

---

## 12. Success Metrics

| Metric | Target (90 days post-launch) |
|--------|------------------------------|
| Registered users | 500+ |
| Applications tracked | 10,000+ |
| % of apps added via email forwarding | ≥30% |
| D30 user retention | ≥40% |
| Avg. applications per active user | ≥15 |
| Users with completed AI profile | ≥60% of registered users |
| AI feature weekly active usage | ≥50% of active users |
| Cover letters / CV tailors generated | 5,000+ |
| Avg. AI response rating | ≥4.0 / 5.0 |
