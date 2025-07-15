"""
Celery configuration for CV Project.
"""
import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("core")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Configure Celery settings
app.conf.update(
    broker_url=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    result_backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_pool="eventlet",  # For Windows compatibility
    worker_concurrency=2,
    task_routes={
        "main.tasks.send_cv_pdf_email": {"queue": "email"},
        "main.tasks.cleanup_old_request_logs": {"queue": "maintenance"},
    },
    beat_schedule={
        "cleanup-old-logs": {
            "task": "main.tasks.cleanup_old_request_logs",
            "schedule": 86400.0,  # Run daily
        },
    },
)

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
