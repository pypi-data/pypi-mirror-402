from .models import IssueCaptureSettings


def issue_capture_settings(request):  # noqa: ARG001
    """Provide issue capture settings to template context."""
    settings = IssueCaptureSettings.get_solo()
    return {
        "issue_capture_enabled": settings.enabled,
        "issue_capture_settings": settings,
    }
