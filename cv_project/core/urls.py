"""
URL configuration for CVProject project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("main.api_urls")),
    path("", include("main.urls")),
]

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0]
    )
