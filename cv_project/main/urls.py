"""
URL configuration for main app.
"""

from django.urls import path
from . import views

urlpatterns = [
    path("", views.CVListView.as_view(), name="cv_list"),
    path("cv/<int:pk>/", views.CVDetailView.as_view(), name="cv_detail"),
    path("cv/<int:pk>/pdf/", views.cv_pdf_download, name="cv_pdf_download"),
    path("cv/<int:pk>/email/", views.email_cv_view, name="cv_email"),
    path("cv/<int:pk>/translate/", views.translate_cv_view, name="cv_translate"),
    path(
        "task-status/<str:task_id>/",
        views.check_email_task_status,
        name="check_task_status",
    ),
    path(
        "translation-status/<str:task_id>/",
        views.check_translation_task_status,
        name="check_translation_status",
    ),
    path("logs/", views.RequestLogsView.as_view(), name="request_logs"),
    path("logs/api/", views.request_logs_api, name="request_logs_api"),
    path("settings/", views.SettingsView.as_view(), name="settings"),
    path("api/settings/", views.settings_api, name="settings_api"),
]
