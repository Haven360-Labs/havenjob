"""
URL configuration for config project.
Mounts Django admin and django-ninja API at /api/.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI

from apps.users.api import router as users_router
from apps.tracker.api import router as tracker_router
from apps.notifications.api import router as notifications_router
from apps.ai.api import router as ai_router
from apps.email.api import router as email_router

api = NinjaAPI(title="HavenJob API", version="0.1.0")
api.add_router("/users", users_router)
api.add_router("/tracker", tracker_router)
api.add_router("/notifications", notifications_router)
api.add_router("/ai", ai_router)
api.add_router("/email", email_router)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
