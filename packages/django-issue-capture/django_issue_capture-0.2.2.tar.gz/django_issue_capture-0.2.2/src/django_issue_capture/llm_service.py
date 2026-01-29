import contextlib
import logging

from django.contrib.auth.models import User
from litellm import completion

from .models import Issue, IssueCaptureSettings, IssueTemplate

logger = logging.getLogger(__name__)


class LLMGenerationError(Exception):
    """Exception raised when LLM generation fails."""


class IssueLLMService:
    """Service for single-shot LLM-powered issue generation."""

    def __init__(self):
        """Initialize the service with LLM configuration from settings."""
        # Get singleton settings
        self.settings = IssueCaptureSettings.get_solo()

        # Validate LLM is configured
        if not self.settings.show_ai_interface:
            raise ValueError(
                "AI interface is disabled in Issue Capture Settings. Enable 'Show AI Interface' in Django admin."
            )

        if not self.settings.llm_api_key:
            raise ValueError(
                "No LLM API key configured. Please set it in Issue Capture Settings (Django admin) "
                "or via ISSUE_CAPTURE_LLM_API_KEY environment variable."
            )

        # Set LLM configuration from settings
        self.api_key = self.settings.llm_api_key
        self.llm_model = self.settings.llm_model
        self.temperature = self.settings.llm_temperature
        self.max_tokens = self.settings.llm_max_tokens

    def generate_comprehensive_issue(
        self, title: str, description: str, template_name: str = "bug", user: User | None = None, reported_url: str = ""
    ) -> dict[str, str]:
        """Generate a comprehensive issue from basic input using direct markdown generation.

        Args:
            title: Basic issue title
            description: User's description of the issue
            template_name: Type of issue template to use
            user: User creating the issue (optional)
            reported_url: URL where issue was reported

        Returns:
            Dictionary with markdown content ready for creation

        """
        try:
            template = IssueTemplate.objects.get(name=template_name, is_active=True)
        except IssueTemplate.DoesNotExist:
            template = None

        # Use generation prompt from template or default
        if template and template.generation_prompt:
            system_prompt = template.generation_prompt
        else:
            system_prompt = self._get_default_generation_prompt()

        # Create comprehensive prompt for markdown generation
        title_instruction = (
            "Create a clear, actionable title" if not title.strip() else "Enhance and improve the provided title"
        )

        user_prompt = f"""
        Generate a comprehensive GitHub-style issue from this input:

        Original Title: {title if title.strip() else "(no title provided - please create one)"}
        Original Description: {description}
        Issue Type: {template_name if template else "general"}

        Please create a well-structured issue with the following sections in markdown format:

        # {title_instruction}
        [The title should be clear, specific, and actionable. This will be the main issue title.]

        ## Description
        [Detailed description with proper context, using markdown formatting like lists, code blocks, etc.]

        ## Acceptance Criteria
        [Clear, testable acceptance criteria as a checklist]

        ## Technical Specifications
        [Technical implementation details and requirements]

        ## Implementation Hints
        [Helpful hints for developers working on this issue]

        ## Metadata
        Priority: [low/medium/high/urgent]
        Complexity: [low/medium/high/very-high]
        Labels: [comma-separated list of relevant labels]
        Confidence: [0.0-1.0 confidence in the analysis]

        Generate comprehensive, actionable content that developers can use to implement this issue.
        """

        # Use litellm for API call
        try:
            completion_kwargs = {
                "api_key": self.api_key,
                "model": self.llm_model,
                "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                "max_tokens": self.max_tokens,
            }
            # Only pass temperature if explicitly set (let provider use its default otherwise)
            if self.temperature is not None:
                completion_kwargs["temperature"] = self.temperature

            response = completion(**completion_kwargs)

            markdown_content = response.choices[0].message.content

            # Extract title from markdown if title was empty
            final_title = title
            if not title.strip():
                import re

                # Look for the first # heading in the markdown
                title_match = re.search(r"^# (.+)$", markdown_content, re.MULTILINE)
                final_title = title_match.group(1).strip() if title_match else "Generated Issue"

            # Return the raw markdown with extracted title
            return {"title": final_title, "description": markdown_content, "template_name": template_name}

        except Exception as e:
            logger.exception("Error in comprehensive generation")
            # Ride or die - if LLM fails, we fail
            raise LLMGenerationError(f"LLM generation failed: {e!s}") from e

    def create_issue_from_generated_data(
        self, generated_data: dict[str, str], user: User, reported_url: str = ""
    ) -> Issue:
        """Create an Issue object from generated markdown data.

        Args:
            generated_data: Dictionary with title, description (markdown), template_name
            user: User creating the issue
            reported_url: URL where issue was reported

        Returns:
            Created Issue instance

        """
        # Get template if specified
        template = None
        if generated_data.get("template_name"):
            with contextlib.suppress(IssueTemplate.DoesNotExist):
                template = IssueTemplate.objects.get(name=generated_data["template_name"], is_active=True)

        # Create the issue with markdown description
        issue = Issue.objects.create(
            title=generated_data["title"],
            description=generated_data["description"],  # Raw markdown from LLM
            status="open",
            priority="medium",  # Default priority
            reported_url=reported_url or "https://example.com",
            user_agent="LLM Generated",
            reported_by=user,
            creation_mode="ai_generated",
            template=template,
            llm_confidence_score=0.8,  # Default confidence
        )

        logger.info("Created comprehensive issue %s for user %s", issue.short_uuid, user.username)
        return issue

    def quick_enhance(self, title: str, description: str, template_name: str = "bug") -> dict[str, str]:
        """Perform quick one-shot enhancement of an issue using direct markdown.

        Args:
            title: Issue title
            description: Issue description
            template_name: Template to use for enhancement

        Returns:
            Dictionary with enhanced content

        """
        # Redirect to comprehensive generation - they're now the same approach
        return self.generate_comprehensive_issue(title=title, description=description, template_name=template_name)

    def _get_default_generation_prompt(self) -> str:
        """Get default generation prompt."""
        return """
        You are creating a comprehensive issue report that will be used by developers and coding agents.

        Structure the issue with:
        - Clear, descriptive title
        - Detailed description with all context
        - Step-by-step reproduction instructions (if applicable)
        - Expected vs actual behavior
        - Acceptance criteria
        - Technical implementation hints
        - Appropriate labels and priority

        Make it actionable and complete.
        """

    def _get_default_enhancement_prompt(self) -> str:
        """Get default enhancement prompt."""
        return """
        Enhance this {template_name}:

        Title: {title}
        Description: {description}

        Add missing details like:
        - Clear reproduction steps
        - Expected vs actual behavior
        - Acceptance criteria
        - Technical context
        - Implementation suggestions

        Make it comprehensive and actionable.
        """
