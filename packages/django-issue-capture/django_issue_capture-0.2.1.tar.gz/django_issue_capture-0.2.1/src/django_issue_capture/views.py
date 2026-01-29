import contextlib
import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods

from .llm_service import IssueLLMService
from .models import Issue, IssueTemplate

logger = logging.getLogger(__name__)

User = get_user_model()


def _check_staff_permissions(user: User) -> bool:
    """Check if user has staff or superuser permissions."""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@login_required
@require_http_methods(["GET", "POST"])
def create_issue(request: HttpRequest) -> HttpResponse:
    """Create a new issue via HTMX form."""
    if not _check_staff_permissions(request.user):
        return HttpResponse(status=403)

    if request.method == "GET":
        # Return the dual-mode interface
        context = {
            "reported_url": request.GET.get("url", ""),
        }
        return render(request, "django_issue_capture/dual_mode_interface.html", context)

    # POST - handle form submission
    title = request.POST.get("title", "").strip()
    description = request.POST.get("description", "").strip()
    reported_url = request.POST.get("reported_url", "").strip()
    priority = request.POST.get("priority", "medium")

    # Basic validation
    if not title:
        return render(
            request,
            "django_issue_capture/_create_form.html",
            {
                "errors": {"title": "Title is required"},
                "title": title,
                "description": description,
                "reported_url": reported_url,
                "priority": priority,
            },
        )

    if not description:
        return render(
            request,
            "django_issue_capture/_create_form.html",
            {
                "errors": {"description": "Description is required"},
                "title": title,
                "description": description,
                "reported_url": reported_url,
                "priority": priority,
            },
        )

    # Get enhanced fields from the form (if provided)
    creation_mode = request.POST.get("creation_mode", "form")
    acceptance_criteria = request.POST.get("acceptance_criteria", "")
    technical_specifications = request.POST.get("technical_specifications", "")
    implementation_hints = request.POST.get("implementation_hints", "")
    estimated_complexity = request.POST.get("estimated_complexity", "")
    suggested_labels = request.POST.get("suggested_labels", "")

    # Get template if specified
    template = None
    template_name = request.POST.get("template")
    if template_name:
        with contextlib.suppress(IssueTemplate.DoesNotExist):
            template = IssueTemplate.objects.get(name=template_name, is_active=True)

    # Create the issue
    issue = Issue.objects.create(
        title=title,
        description=description,
        reported_url=reported_url or request.META.get("HTTP_REFERER", ""),
        priority=priority,
        reported_by=request.user,
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
        creation_mode=creation_mode,
        template=template,
        acceptance_criteria=acceptance_criteria,
        technical_specifications=technical_specifications,
        implementation_hints=implementation_hints,
        estimated_complexity=estimated_complexity,
        suggested_labels=suggested_labels,
        payload={
            "created_via": "htmx_form",
            "remote_addr": request.META.get("REMOTE_ADDR", ""),
            "enhanced_fields": bool(acceptance_criteria or technical_specifications or implementation_hints),
        },
    )

    # Return success notification
    return render(request, "django_issue_capture/_success_notification.html", {"issue": issue})


@login_required
def issue_detail(request: HttpRequest, short_uuid: str) -> HttpResponse:
    """View issue details (staff/superuser only)."""
    if not _check_staff_permissions(request.user):
        return HttpResponse(status=403)

    issue = get_object_or_404(Issue, short_uuid=short_uuid)
    return render(request, "django_issue_capture/detail.html", {"issue": issue})


@login_required
def issue_list(request: HttpRequest) -> HttpResponse:
    """List all issues (staff/superuser only)."""
    if not _check_staff_permissions(request.user):
        return HttpResponse(status=403)

    issues = Issue.objects.select_related("reported_by", "assigned_to").all()

    # Filter by status if provided
    status_filter = request.GET.get("status")
    if status_filter:
        issues = issues.filter(status=status_filter)

    return render(
        request,
        "django_issue_capture/list.html",
        {
            "issues": issues,
            "status_filter": status_filter,
            "status_choices": Issue.STATUS_CHOICES,
        },
    )


@login_required
@require_http_methods(["POST"])
def generate_comprehensive_issue(request: HttpRequest) -> HttpResponse:
    """Generate a comprehensive issue using single-shot LLM generation."""
    if not _check_staff_permissions(request.user):
        return HttpResponse(status=403)

    title = request.POST.get("title", "").strip()
    description = request.POST.get("description", "").strip()
    template_name = request.POST.get("template", "bug")
    action = request.POST.get("action", "preview")  # preview or create

    if not description:
        return JsonResponse({"error": "Description is required"}, status=400)

    try:
        llm_service = IssueLLMService()
        generated = llm_service.generate_comprehensive_issue(
            title=title or "Issue Title",
            description=description,
            template_name=template_name,
            user=request.user,
            reported_url=request.POST.get("reported_url", ""),
        )

        if action == "create":
            # Create the issue directly
            issue = llm_service.create_issue_from_generated_data(
                generated_data=generated, user=request.user, reported_url=request.POST.get("reported_url", "")
            )
            return render(request, "django_issue_capture/_success_notification.html", {"issue": issue})
        # Show preview for editing
        return render(
            request,
            "django_issue_capture/_issue_preview.html",
            {"generated": generated, "template_name": template_name},
        )

    except Exception as e:
        logger.exception("Error generating comprehensive issue")

        # Return user-friendly error message
        error_message = "AI generation failed. This could be due to API issues or service downtime."
        if "LLM generation failed" in str(e):
            error_message = "The AI service is currently unavailable. Please try again in a moment."

        return render(
            request,
            "django_issue_capture/_generation_error.html",
            {"error": error_message, "title": title, "description": description, "template_name": template_name},
        )


@login_required
@require_http_methods(["POST"])
def quick_enhance_issue(request: HttpRequest) -> HttpResponse:
    """Quick enhance an issue using LLM (legacy mode - redirects to comprehensive generation)."""
    if not _check_staff_permissions(request.user):
        return HttpResponse(status=403)

    # Redirect to the new comprehensive generation
    return generate_comprehensive_issue(request)
