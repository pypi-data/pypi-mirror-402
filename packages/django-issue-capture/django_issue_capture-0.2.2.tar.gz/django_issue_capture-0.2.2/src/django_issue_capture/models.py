from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from shortuuid.django_fields import ShortUUIDField
from solo.models import SingletonModel


class IssueTemplate(models.Model):
    """Template for different types of issues with AI generation prompts."""

    TEMPLATE_CHOICES = [
        ("bug", "Bug Report"),
        ("feature", "Feature Request"),
        ("task", "Task"),
        ("enhancement", "Enhancement"),
        ("question", "Question"),
    ]

    name = models.CharField(max_length=100, choices=TEMPLATE_CHOICES, unique=True)
    display_name = models.CharField(max_length=100, help_text="Human-friendly name")
    description = models.TextField(help_text="Description of when to use this template")

    # Required context fields (for reference in generation)
    required_context = models.JSONField(
        default=list,
        help_text="List of context fields to include in generated issues (e.g., 'steps_to_reproduce', 'expected_behavior')",
    )

    # LLM generation prompt
    generation_prompt = models.TextField(help_text="System prompt for AI-powered issue generation")

    # Default GitHub labels
    default_labels = models.CharField(
        max_length=200, blank=True, help_text="Comma-separated list of default GitHub labels for this issue type"
    )

    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Issue Template"
        verbose_name_plural = "Issue Templates"
        ordering = ["name"]

    def __str__(self) -> str:
        """Return string representation of the template."""
        return self.display_name

    @property
    def required_context_count(self) -> int:
        """Return the number of required context fields."""
        return len(self.required_context) if self.required_context else 0


class Issue(models.Model):
    """Represents an issue reported by a user, capturing essential details."""

    STATUS_CHOICES = [
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
        ("closed", "Closed"),
    ]

    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("urgent", "Urgent"),
    ]

    short_uuid = ShortUUIDField(unique=True, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="medium")

    # Context capture
    reported_url = models.URLField(help_text="URL where the issue was reported from")
    user_agent = models.TextField(blank=True, help_text="Browser user agent string")

    # User info
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reported_issues")
    assigned_to = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_issues"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Flexible metadata storage
    payload = models.JSONField(default=dict, blank=True, help_text="Additional issue metadata")

    # LLM-generated content fields
    acceptance_criteria = models.TextField(
        blank=True, default="", help_text="AI-generated acceptance criteria for the issue"
    )
    technical_specifications = models.TextField(
        blank=True, default="", help_text="AI-generated technical specifications and implementation details"
    )
    implementation_hints = models.TextField(
        blank=True, default="", help_text="AI-generated hints and suggestions for implementation"
    )
    estimated_complexity = models.CharField(
        max_length=20, blank=True, default="", help_text="AI-estimated complexity level (low, medium, high, very-high)"
    )
    suggested_labels = models.TextField(
        blank=True, default="", help_text="AI-suggested GitHub labels (comma-separated)"
    )

    # Issue creation mode and template
    CREATION_MODE_CHOICES = [
        ("form", "Standard Form"),
        ("ai_generated", "AI Generated"),
    ]

    creation_mode = models.CharField(
        max_length=15, choices=CREATION_MODE_CHOICES, default="form", help_text="How this issue was created"
    )
    template = models.ForeignKey(
        IssueTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="issues",
        help_text="Template used for this issue (if any)",
    )

    # LLM confidence tracking
    llm_confidence_score = models.FloatField(
        null=True, blank=True, help_text="AI confidence score in the generated content (0.0 to 1.0)"
    )

    # GitHub promotion tracking
    github_url = models.URLField(blank=True, help_text="URL of the GitHub issue if promoted")
    github_issue_number = models.PositiveIntegerField(
        null=True, blank=True, help_text="GitHub issue number if promoted"
    )
    github_promoted_at = models.DateTimeField(null=True, blank=True, help_text="When the issue was promoted to GitHub")
    github_promoted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="promoted_issues",
        help_text="User who promoted the issue to GitHub",
    )

    class Meta:
        """Meta options for the Issue model."""

        ordering = ["-created_at"]
        verbose_name = "Issue"
        verbose_name_plural = "Issues"

    def __str__(self) -> str:
        """Return a string representation of the issue."""
        return f"#{self.short_uuid}: {self.title}"

    def get_absolute_url(self) -> str:
        """Return the absolute URL for the issue detail view."""
        return reverse("django_issue_capture:detail", kwargs={"short_uuid": self.short_uuid})

    @property
    def is_promoted_to_github(self) -> bool:
        """Return True if the issue has been promoted to GitHub."""
        return bool(self.github_url and self.github_issue_number)


class IssueCaptureSettings(SingletonModel):
    """Singleton model for issue capture configuration including GitHub and LLM settings."""

    # Feature toggle
    enabled = models.BooleanField(default=True, help_text="Enable issue capture floating button for staff/superusers")
    staff_only = models.BooleanField(
        default=True,
        help_text="If True, only staff/superusers see the issue button. If False, all authenticated users see it.",
    )

    # GitHub integration (REQUIRED for promotion)
    github_repo = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="GitHub repository in format: owner/repo (e.g., 'octocat/Hello-World')",
    )
    github_api_key = models.CharField(
        max_length=255, blank=True, default="", help_text="GitHub Personal Access Token with repo access"
    )
    github_label = models.CharField(
        max_length=50, default="issue-capture", help_text="Label to apply to created GitHub issues"
    )

    # LLM integration (REQUIRED for AI features)
    llm_api_key = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="API key for LLM provider (OpenAI, Anthropic, etc.). Set via environment for production.",
    )
    llm_model = models.CharField(
        max_length=100,
        default="gpt-4o-mini",
        help_text=(
            "LiteLLM model identifier. Format: provider/model-name. "
            "Examples: gpt-4o-mini (OpenAI), anthropic/claude-3-5-sonnet-20241022, ollama_chat/llama3"
        ),
    )
    show_ai_interface = models.BooleanField(default=True, help_text="Show AI Generate tab in issue creation interface")
    llm_temperature = models.FloatField(
        null=True,
        blank=True,
        default=None,
        help_text=(
            "Leave blank to use provider's default. "
            "If set: 0.0 = deterministic, higher = more creative. "
            "Note: Anthropic range is 0-1, OpenAI range is 0-2."
        ),
    )
    llm_max_tokens = models.PositiveIntegerField(
        default=2000, help_text="Maximum tokens for LLM generation (higher = longer responses)"
    )

    class Meta:
        verbose_name = "Issue Capture Settings"

    def clean(self):
        """Validate settings before saving."""
        # Validate GitHub repo format (owner/repo)
        if self.github_repo and "/" not in self.github_repo:
            raise ValidationError({"github_repo": "Repository must be in format: owner/repo"})

        # Validate GitHub API key format (basic validation)
        if self.github_api_key:
            if len(self.github_api_key) < 20:
                raise ValidationError(
                    {"github_api_key": "GitHub API key appears to be too short. Please check your token."}
                )
            if not self.github_api_key.startswith(("ghp_", "gho_", "ghu_", "ghs_", "ghr_", "github_pat_")):
                raise ValidationError(
                    {"github_api_key": "GitHub API key should start with ghp_, gho_, ghu_, ghs_, ghr_, or github_pat_"}
                )

        # Validate LLM temperature range (if set)
        if self.llm_temperature is not None:
            if self.llm_temperature < 0.0 or self.llm_temperature > 2.0:
                raise ValidationError({"llm_temperature": "Temperature must be between 0.0 and 2.0"})

        # Validate LLM max tokens
        if self.llm_max_tokens < 100 or self.llm_max_tokens > 10000:
            raise ValidationError({"llm_max_tokens": "Max tokens must be between 100 and 10,000"})

    def __str__(self):
        """Return string representation of issue capture settings."""
        return "Issue Capture Settings"

    @property
    def llm_configuration_errors(self) -> list[str]:
        """Return list of LLM configuration errors, empty if properly configured."""
        errors = []
        if not self.llm_api_key:
            errors.append("API key required. Configure in Django Admin → Issue Capture Settings.")
        if not self.llm_model:
            errors.append("LLM model required. Configure in Django Admin → Issue Capture Settings.")
        return errors
