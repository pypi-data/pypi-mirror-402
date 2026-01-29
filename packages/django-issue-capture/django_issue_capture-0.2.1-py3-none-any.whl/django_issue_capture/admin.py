from django.contrib import admin, messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import path, reverse
from django.utils.html import format_html
from solo.admin import SingletonModelAdmin

from .models import Issue, IssueCaptureSettings, IssueTemplate
from .services import GitHubError, GitHubService


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    """Admin interface for managing issues reported by users."""

    list_display = ["short_uuid", "title", "status", "priority", "reported_by", "created_at", "github_promotion_status"]
    list_filter = ["status", "priority", "created_at", "reported_by", "github_promoted_at"]
    search_fields = ["title", "description", "short_uuid"]
    readonly_fields = [
        "short_uuid",
        "created_at",
        "updated_at",
        "reported_url_link",
        "github_url",
        "github_issue_number",
        "github_promoted_at",
        "github_promoted_by",
    ]

    fieldsets = [
        ("Issue Details", {"fields": ["short_uuid", "title", "description", "status", "priority"]}),
        ("Assignment", {"fields": ["reported_by", "assigned_to"]}),
        ("Context", {"fields": ["reported_url_link", "user_agent"]}),
        (
            "GitHub Promotion",
            {
                "fields": ["github_url", "github_issue_number", "github_promoted_at", "github_promoted_by"],
                "classes": ["collapse"],
            },
        ),
        ("Timestamps", {"fields": ["created_at", "updated_at"]}),
        ("Additional Data", {"fields": ["payload"], "classes": ["collapse"]}),
    ]

    class Media:
        js = ("admin/js/jquery.min.js", "https://unpkg.com/htmx.org@2.0.1/dist/htmx.min.js")
        css = {"all": ("admin/css/changelists.css",)}

    def reported_url_link(self, obj: Issue) -> str:
        """Return a clickable link for the reported URL."""
        if obj.reported_url:
            return format_html('<a href="{}" target="_blank">{}</a>', obj.reported_url, obj.reported_url)
        return "-"

    reported_url_link.short_description = "Reported URL"

    def github_promotion_status(self, obj: Issue) -> str:
        """Return promotion status with button or link."""
        if obj.is_promoted_to_github:
            return format_html(
                '<a href="{}" target="_blank" class="button" style="background-color: #28a745; color: white; text-decoration: none; padding: 4px 8px; border-radius: 3px; font-size: 11px;">GitHub #{}</a>',
                obj.github_url,
                obj.github_issue_number,
            )
        promote_url = reverse("admin:django_issue_capture_issue_promote", args=[obj.pk])
        return format_html(
            "<button "
            'hx-post="{}" '
            'hx-target="closest tr" '
            'hx-swap="outerHTML" '
            'hx-include="[name=csrfmiddlewaretoken]" '
            'class="button" '
            'style="background-color: #007cba; color: white; border: none; padding: 4px 8px; border-radius: 3px; font-size: 11px; cursor: pointer;">'
            "Promote"
            "</button>",
            promote_url,
        )

    github_promotion_status.short_description = "GitHub"
    github_promotion_status.allow_tags = True

    def get_urls(self):
        """Add custom URLs for HTMX endpoints."""
        urls = super().get_urls()
        custom_urls = [
            path("<int:issue_id>/promote/", self.promote_issue_view, name="django_issue_capture_issue_promote"),
        ]
        return custom_urls + urls

    def promote_issue_view(self, request, issue_id):
        """HTMX endpoint to promote an issue to GitHub."""
        if not request.user.is_staff:
            return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)

        try:
            issue = get_object_or_404(Issue, pk=issue_id)

            if issue.is_promoted_to_github:
                return HttpResponse('<div class="alert alert-warning">Issue already promoted</div>', status=400)

            github_service = GitHubService()
            github_service.promote_issue(issue, request.user)

            # Refresh the issue from database to get updated fields
            issue.refresh_from_db()

            # Return updated table row
            return render(request, "django_issue_capture/admin_row_update.html", {"issue": issue})

        except GitHubError as e:
            return HttpResponse(f'<div class="alert alert-danger">GitHub Error: {e!s}</div>', status=400)

        except Exception as e:
            return HttpResponse(f'<div class="alert alert-danger">Unexpected error: {e!s}</div>', status=500)


@admin.register(IssueCaptureSettings)
class IssueCaptureSettingsAdmin(SingletonModelAdmin):
    fieldsets = [
        ("Feature Toggle", {"fields": ["enabled"]}),
        (
            "LLM Configuration",
            {
                "fields": ["show_ai_interface", "llm_api_key", "llm_model", "llm_temperature", "llm_max_tokens"],
                "description": "Configure LLM for AI-powered issue generation",
            },
        ),
        (
            "GitHub Integration",
            {
                "fields": ["github_repo", "github_api_key", "github_label"],
                "description": "Configure GitHub repository and API access for issue promotion",
            },
        ),
    ]

    def save_model(self, request, obj, form, change):
        """Save model and test GitHub connection if configured."""
        super().save_model(request, obj, form, change)

        # Test GitHub connection if all fields are provided
        if obj.github_repo and obj.github_api_key:
            try:
                github_service = GitHubService()
                success, message = github_service.test_connection()
                if success:
                    self.message_user(request, f"GitHub connection successful: {message}", level=messages.SUCCESS)
                else:
                    self.message_user(request, f"GitHub connection failed: {message}", level=messages.WARNING)
            except Exception as e:
                self.message_user(request, f"GitHub connection test error: {e!s}", level=messages.ERROR)


@admin.register(IssueTemplate)
class IssueTemplateAdmin(admin.ModelAdmin):
    """Admin interface for managing issue templates."""

    list_display = [
        "display_name",
        "name",
        "is_active",
        "required_context_count",
        "created_at",
    ]
    list_filter = ["is_active", "name", "created_at"]
    search_fields = ["display_name", "description"]

    fieldsets = [
        ("Basic Information", {"fields": ["name", "display_name", "description", "is_active"]}),
        ("Context Settings", {"fields": ["required_context"]}),
        ("LLM Generation", {"fields": ["generation_prompt"], "classes": ["collapse"]}),
        ("GitHub Integration", {"fields": ["default_labels"]}),
    ]

    def required_context_count(self, obj):
        """Display count of required context fields."""
        return obj.required_context_count

    required_context_count.short_description = "Required Context Fields"
