from ninja import Router

from apps.tracker.models import Application, ApplicationStatusHistory, StatusChangedBy
from apps.tracker.schemas import ApplicationIn, ApplicationOut, ApplicationStatusUpdateIn

router = Router(tags=["tracker"])


@router.get("", response={200: list[ApplicationOut], 401: dict})
def list_applications(request):
    """List the current user's job applications, sorted by date applied (newest first)."""
    if not request.user.is_authenticated:
        return 401, {"detail": "Authentication required"}
    applications = (
        Application.objects.filter(user_id=request.user.id)
        .order_by("-date_applied")
    )
    return 200, list(applications)


@router.get(
    "{application_id}",
    response={200: ApplicationOut, 401: dict, 403: dict, 404: dict},
)
def get_application(request, application_id):
    """Get a single application by id. Requires auth; must own the application."""
    if not request.user.is_authenticated:
        return 401, {"detail": "Authentication required"}
    try:
        application = Application.objects.get(pk=application_id)
    except Application.DoesNotExist:
        return 404, {"detail": "Application not found"}
    if application.user_id != request.user.id:
        return 403, {"detail": "Forbidden"}
    return 200, application


@router.post("", response={201: ApplicationOut, 401: dict})
def create_application(request, payload: ApplicationIn):
    """Create a new job application (manual add). Requires authenticated user."""
    if not request.user.is_authenticated:
        return 401, {"detail": "Authentication required"}
    job_url = payload.job_url
    if job_url is not None and hasattr(job_url, "unicode_string"):
        job_url = job_url.unicode_string()
    application = Application.objects.create(
        user_id=request.user.id,
        company_name=payload.company_name,
        job_title=payload.job_title,
        date_applied=payload.date_applied,
        status=payload.status,
        source=payload.source,
        notes=payload.notes,
        deadline=payload.deadline,
        follow_up_date=payload.follow_up_date,
        job_url=job_url,
        location=payload.location,
        salary_min=payload.salary_min,
        salary_max=payload.salary_max,
        salary_currency=payload.salary_currency,
    )
    return 201, application


@router.patch(
    "{application_id}",
    response={200: ApplicationOut, 401: dict, 403: dict, 404: dict},
)
def update_application_status(request, application_id, payload: ApplicationStatusUpdateIn):
    """Update an application's status and log the change to history. Requires auth; must own the application."""
    if not request.user.is_authenticated:
        return 401, {"detail": "Authentication required"}
    try:
        application = Application.objects.get(pk=application_id)
    except Application.DoesNotExist:
        return 404, {"detail": "Application not found"}
    if application.user_id != request.user.id:
        return 403, {"detail": "Forbidden"}
    old_status = application.status
    new_status = payload.status
    if old_status != new_status:
        application.status = new_status
        application.save(update_fields=["status", "updated_at"])
        ApplicationStatusHistory.objects.create(
            application=application,
            old_status=old_status,
            new_status=new_status,
            changed_by=StatusChangedBy.USER,
        )
    return 200, application
