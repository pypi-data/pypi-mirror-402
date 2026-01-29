from django.apps import AppConfig


class IssueCaptureConfig(AppConfig):
    """Configuration for the Issue Capture app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "django_issue_capture"
    label = "django_issue_capture"  # Clean table names: django_issue_capture_*
    verbose_name = "Issue Capture"
