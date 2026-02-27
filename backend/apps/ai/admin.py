"""Django admin registration for the AI app models."""

from django.contrib import admin
from .models import (
    Education,
    WorkExperience,
    Project,
    CVDocument,
    JobDescription,
    InterviewQuestion,
    UserAnswer,
    ChatSession,
    ChatMessage,
    AIOutput,
)


@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ("institution", "degree", "user", "start_date", "end_date", "is_current", "display_order")
    list_filter = ("is_current",)
    search_fields = ("institution", "degree", "field_of_study", "user__email")
    raw_id_fields = ("user",)
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(WorkExperience)
class WorkExperienceAdmin(admin.ModelAdmin):
    list_display = ("company", "role", "user", "start_date", "end_date", "is_current", "display_order")
    list_filter = ("is_current",)
    search_fields = ("company", "role", "user__email")
    raw_id_fields = ("user",)
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "display_order", "created_at")
    search_fields = ("title", "user__email")
    raw_id_fields = ("user",)
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(CVDocument)
class CVDocumentAdmin(admin.ModelAdmin):
    list_display = ("file_name", "user", "is_primary", "uploaded_at")
    list_filter = ("is_primary",)
    search_fields = ("file_name", "user__email")
    raw_id_fields = ("user",)
    readonly_fields = ("id", "uploaded_at")


@admin.register(JobDescription)
class JobDescriptionAdmin(admin.ModelAdmin):
    list_display = ("job_title", "company_name", "user", "application", "created_at")
    search_fields = ("job_title", "company_name", "user__email")
    raw_id_fields = ("user", "application")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(InterviewQuestion)
class InterviewQuestionAdmin(admin.ModelAdmin):
    list_display = ("category", "question_type", "question_preview", "created_at")
    list_filter = ("category", "question_type")
    search_fields = ("category", "question")

    def question_preview(self, obj):
        return obj.question[:80] + "..." if len(obj.question) > 80 else obj.question

    question_preview.short_description = "Question"


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ("user", "question", "custom_question_preview", "is_ai_generated", "updated_at")
    list_filter = ("is_ai_generated",)
    search_fields = ("user__email", "custom_question", "draft_answer")
    raw_id_fields = ("user", "question")
    readonly_fields = ("id", "created_at", "updated_at")

    def custom_question_preview(self, obj):
        if obj.custom_question:
            return obj.custom_question[:60] + "..." if len(obj.custom_question) > 60 else obj.custom_question
        return "—"

    custom_question_preview.short_description = "Custom question"


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ("id", "role", "content", "token_count", "created_at")
    max_num = 20


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "title", "created_at", "updated_at")
    search_fields = ("title", "user__email")
    raw_id_fields = ("user",)
    readonly_fields = ("id", "created_at", "updated_at")
    inlines = (ChatMessageInline,)


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("session", "role", "content_preview", "token_count", "created_at")
    list_filter = ("role",)
    search_fields = ("content", "session__user__email")
    raw_id_fields = ("session",)
    readonly_fields = ("id", "created_at")

    def content_preview(self, obj):
        return obj.content[:80] + "..." if len(obj.content) > 80 else obj.content

    content_preview.short_description = "Content"


@admin.register(AIOutput)
class AIOutputAdmin(admin.ModelAdmin):
    list_display = ("type", "user", "job_description", "application", "created_at")
    list_filter = ("type",)
    search_fields = ("user__email", "content")
    raw_id_fields = ("user", "job_description", "application")
    readonly_fields = ("id", "created_at")
