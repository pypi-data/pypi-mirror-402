# CLAUDE.md - Django Issue Capture Package

This file provides guidance to Claude Code when working with the `django-issue-capture` package.

## Project Overview

**Django Issue Capture** is a standalone Django package providing AI-powered GitHub issue creation and management with LLM enhancement via LiteLLM and direct GitHub integration.

**Key Features**:
- AI-powered issue generation with model optionality (LiteLLM)
- Self-contained LLM configuration via Django Solo
- Single-shot AI generation workflow (quick and efficient)
- GitHub API integration for issue promotion
- Template system for different issue types
- HTMX-powered admin interface
- Markdown rendering with sanitization

## Package Structure

```
django-issue-capture/
├── src/django_issue_capture/
│   ├── __init__.py (version export)
│   ├── apps.py (app label: django_issue_capture)
│   ├── models.py (3 models: Issue, IssueTemplate, IssueCaptureSettings)
│   ├── admin.py (HTMX admin with promotion)
│   ├── views.py (5 views)
│   ├── urls.py
│   ├── services.py (GitHub API)
│   ├── llm_service.py (LiteLLM integration)
│   ├── context_processors.py
│   ├── management/commands/setup_issue_templates.py
│   ├── templates/django_issue_capture/ (9 templates)
│   └── migrations/
├── tests/
│   ├── settings.py (standalone test config)
│   ├── manage.py
│   ├── urls.py
│   └── test_*.py (3 test files)
├── pyproject.toml
├── README.md (user documentation)
├── CLAUDE.md (this file)
├── Makefile (development commands)
└── LICENSE (MIT)
```

## Development Setup

This package is part of the Directory Platform workspace. Use UV for dependency management:

```bash
# From package directory
cd django-issue-capture
uv sync --extra dev

# Or from workspace root
uv sync
```

## Code Patterns

### App Label and Namespacing

The app uses an explicit label for clean table names:

```python
# apps.py
class IssueCaptureConfig(AppConfig):
    name = "django_issue_capture"
    label = "django_issue_capture"  # Clean tables: django_issue_capture_*
```

**Result**: Clean table names without `db_table` overrides:
- `django_issue_capture_issue`
- `django_issue_capture_issuetemplate`
- `django_issue_capture_issuecapturesettings`

### Self-Contained LLM Configuration

No external `llm_suite` dependency. All LLM config is in the singleton settings model:

```python
class IssueCaptureSettings(SingletonModel):
    # Feature toggle
    enabled = BooleanField(default=True)

    # GitHub (REQUIRED)
    github_repo = CharField(...)
    github_api_key = CharField(...)

    # LLM (REQUIRED)
    llm_api_key = CharField(...)
    llm_model = CharField(default="gpt-4o-mini")
    show_ai_interface = BooleanField(default=True)
    llm_temperature = FloatField(null=True, default=None)
    llm_max_tokens = IntegerField(default=2000)
```

### LLM Service Pattern

The service reads from singleton settings:

```python
class IssueLLMService:
    def __init__(self):
        self.settings = IssueCaptureSettings.get_solo()

        if not self.settings.show_ai_interface:
            raise ValueError("AI interface is disabled...")

        self.api_key = self.settings.llm_api_key
        self.llm_model = self.settings.llm_model
```

### URL Namespacing

Uses `django_issue_capture` namespace:

```python
# urls.py
app_name = "django_issue_capture"

# In views/templates
reverse("django_issue_capture:detail", kwargs={"short_uuid": uuid})
```

## Critical Constraints

### NEVER Do These

- ❌ Add external dependencies for LLM config (self-contained)
- ❌ Use `db_table` overrides (we have clean app labels)
- ❌ Import from `directory-builder` apps (must be standalone)
- ❌ Break the GitHub or LLM singleton dependencies
- ❌ Use inline imports

### ALWAYS Do These

- ✅ Keep LLM config in IssueCaptureSettings singleton
- ✅ Use LiteLLM for model optionality
- ✅ Run `make check` before committing
- ✅ Update migrations after model changes
- ✅ Keep tests passing
- ✅ Validate GitHub/LLM settings in `clean()`

## Common Commands

```bash
# Development
make install         # Install dependencies
make migrate         # Run migrations
make shell           # Django shell
make makemigrations  # Create migrations

# Quality
make lint            # Ruff linting
make format          # Auto-format code
make check           # All quality checks
make test            # Run test suite

# Package
make build           # Build package
make clean           # Clean generated files
```

## Testing

```bash
# Run all tests
make test

# Verbose output
PYTHONPATH=. uv run python tests/manage.py test --verbosity=2

# Specific test
PYTHONPATH=. uv run python tests/manage.py test tests.test_models_and_views
```

## Architecture Decisions

### Why Django Solo for Settings?

Self-contained configuration without external dependencies. Users configure once in admin, settings persist in database.

### Why LiteLLM?

Model optionality. Users can use:
- OpenAI (gpt-4o-mini, gpt-4o)
- Anthropic (claude-3-5-sonnet-20241022)
- Ollama (ollama/llama3)
- Any LiteLLM-supported provider

Single `llm_model` field works across all providers.

### Why Markdown + Sanitization?

LLM generates markdown descriptions. `django-markdownify` provides:
- Template tags for easy rendering
- HTML sanitization (security)
- Configurable allowed tags

### Why HTMX in Admin?

One-click GitHub promotion without page reload. Better UX for staff managing issues.

## Extension Points

Users can:
1. **Extend Issue model**: Use Profile Pattern with OneToOneField
2. **Custom templates**: Override in `templates/django_issue_capture/`
3. **Custom issue types**: Add to `IssueTemplate.TEMPLATE_CHOICES`
4. **Additional LLM providers**: Just set `llm_model` to any LiteLLM identifier

## Model Relationships

```
IssueCaptureSettings (Singleton)
    └─> Configuration for GitHub + LLM

IssueTemplate
    └─> Issue (FK)

Issue
    ├─> User (FK - reported_by)
    ├─> User (FK - assigned_to)
    ├─> User (FK - github_promoted_by)
    └─> IssueTemplate (FK)
```

## Dependencies

**Runtime:**
- Django ≥ 4.2
- django-solo ≥ 2.0
- shortuuid ≥ 1.0
- requests ≥ 2.32
- litellm ≥ 1.70
- django-markdownify ≥ 0.9

**Development:**
- ruff (linting and formatting)
- mypy (type checking)
- django-stubs (Django type stubs)

## Configuration Examples

### Basic Setup

```python
# settings.py
INSTALLED_APPS = [
    # ...
    "solo",
    "django_markdownify",
    "django_issue_capture",
]

# Admin configuration via Django admin
# Navigate to Issue Capture Settings:
# - GitHub repo: "owner/repo"
# - GitHub API key: "ghp_..."
# - LLM API key: "sk-..." (OpenAI) or "sk-ant-..." (Anthropic)
# - LLM model: "gpt-4o-mini" or "claude-3-5-sonnet-20241022"
```

### Environment Variables (Production)

```python
# settings.py
import os

# Read from environment, update singleton on startup
ISSUE_CAPTURE_LLM_API_KEY = os.getenv("ISSUE_CAPTURE_LLM_API_KEY")
ISSUE_CAPTURE_GITHUB_API_KEY = os.getenv("GITHUB_API_KEY")

# In AppConfig.ready()
from django_issue_capture.models import IssueCaptureSettings

settings = IssueCaptureSettings.get_solo()
if ISSUE_CAPTURE_LLM_API_KEY:
    settings.llm_api_key = ISSUE_CAPTURE_LLM_API_KEY
if ISSUE_CAPTURE_GITHUB_API_KEY:
    settings.github_api_key = ISSUE_CAPTURE_GITHUB_API_KEY
settings.save()
```

## Troubleshooting

**"No active API key found":**
- Configure LLM API key in Django admin (Issue Capture Settings)
- Ensure `show_ai_interface` is True

**"GitHub API authentication failed":**
- Verify GitHub token has `repo` scope
- Check token format starts with `ghp_`, `gho_`, etc.

**"LLM generation failed":**
- Check API key is valid
- Verify model name is correct (e.g., `gpt-4o-mini` not `gpt-4o-mini-2024`)
- Check LiteLLM logs for provider-specific errors

**Migrations not applying:**
- Verify `django_issue_capture` is in INSTALLED_APPS
- Run `python manage.py migrate django_issue_capture`

## Code Style

- Line length: 120 characters
- Python 3.12+ syntax
- Type hints on public methods
- Google-style docstrings
- Use double quotes for strings

## Related Files

- **workspace CLAUDE.md**: `/Users/samtexas/src/directory-platform/CLAUDE.md`
- **directory-builder CLAUDE.md**: `/Users/samtexas/src/directory-platform/directory-builder/CLAUDE.md`
- **django-seo-audit CLAUDE.md**: `/Users/samtexas/src/directory-platform/django-seo-audit/CLAUDE.md`
- **django-directory-cms CLAUDE.md**: `/Users/samtexas/src/directory-platform/django-directory-cms/CLAUDE.md`
- **README.md**: User-facing documentation
- **pyproject.toml**: Package configuration

## Quick Reference

**Import patterns:**
```python
from django_issue_capture.models import Issue, IssueTemplate, IssueCaptureSettings
from django_issue_capture.services import GitHubService
from django_issue_capture.llm_service import IssueLLMService
```

**URL patterns:**
```python
# Include in project urls.py
path("issues/", include("django_issue_capture.urls")),
```

**Management commands:**
```bash
python manage.py setup_issue_templates  # Initialize templates
```

## Publishing to PyPI

See [RELEASING.md](./RELEASING.md) for the complete release process.

Quick reference:
1. Run checks: `make check && make test`
2. Bump version in `pyproject.toml` and `__init__.py`
3. Commit and push
4. Create release: `gh release create vX.Y.Z`

Use `/publish` command to execute this workflow.
