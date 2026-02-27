from django.contrib import admin
from .models import Application, ApplicationStatusHistory


class ApplicationStatusHistoryInline(admin.TabularInline):
    model = ApplicationStatusHistory
    extra = 0
    readonly_fields = ("id", "old_status", "new_status", "changed_by", "changed_at")


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("job_title", "company_name", "user", "status", "date_applied", "is_needs_review", "created_at")
    list_filter = ("status", "is_needs_review", "date_applied")
    search_fields = ("company_name", "job_title", "user__email")
    raw_id_fields = ("user",)
    readonly_fields = ("id", "created_at", "updated_at")
    date_hierarchy = "date_applied"
    inlines = (ApplicationStatusHistoryInline,)


@admin.register(ApplicationStatusHistory)
class ApplicationStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("application", "old_status", "new_status", "changed_by", "changed_at")
    list_filter = ("changed_by", "new_status")
    search_fields = ("application__job_title", "application__company_name")
    raw_id_fields = ("application",)
    readonly_fields = ("id", "changed_at")
