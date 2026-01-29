# Django Issue Capture

AI-powered GitHub issue creation and management system for Django with LLM enhancement.

## Features

- **AI-Powered Issue Generation**: Use LiteLLM to generate comprehensive issues from basic descriptions
- **Model Optionality**: Support for OpenAI, Anthropic, Ollama, and any LiteLLM-compatible provider
- **GitHub Integration**: Direct promotion of issues to GitHub repositories
- **Template System**: Predefined templates for bugs, features, tasks, and enhancements
- **HTMX Admin**: Interactive admin interface with one-click GitHub promotion
- **Markdown Support**: Full markdown rendering with sanitization

## Installation

```bash
pip install django-issue-capture
```

## Quick Start

1. Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    "solo",  # Required dependency
    "django_markdownify",  # For markdown rendering
    "django_issue_capture",
]
```

2. Add context processor (optional, for floating button):

```python
TEMPLATES = [{
    'OPTIONS': {
        'context_processors': [
            # ...
            'django_issue_capture.context_processors.issue_capture_settings',
        ],
    },
}]
```

3. Include URLs:

```python
from django.urls import include, path

urlpatterns = [
    # ...
    path("issues/", include("django_issue_capture.urls")),
]
```

4. Run migrations:

```bash
python manage.py migrate
```

5. Configure in Django Admin:

Navigate to **Issue Capture Settings** and configure:
- **GitHub**: Repository (`owner/repo`) and Personal Access Token
- **LLM**: API key and model (e.g., `gpt-4o-mini`, `anthropic/claude-3-5-sonnet-20241022`)

6. Set up issue templates:

```bash
python manage.py setup_issue_templates
```

## Configuration

### LLM Models

This package uses [LiteLLM](https://docs.litellm.ai/docs/) for model optionality. Use the format `provider/model-name`:

| Provider | Model Format | API Key Prefix |
|----------|--------------|----------------|
| OpenAI | `gpt-4o-mini`, `gpt-4o` | `sk-...` |
| Anthropic | `anthropic/claude-3-5-sonnet-20241022` | `sk-ant-...` |
| Ollama (local) | `ollama_chat/llama3`, `ollama_chat/mistral` | (none) |
| Azure OpenAI | `azure/deployment-name` | (Azure key) |

> **Note**: OpenAI models work without a prefix. Most other providers require the `provider/` prefix.

See [LiteLLM providers](https://docs.litellm.ai/docs/providers) for the full list.

### GitHub Integration

To promote issues to GitHub, you need a Personal Access Token (PAT) with the appropriate permissions.

#### Creating a Personal Access Token

**Option 1: Fine-grained token (Recommended)**

Fine-grained tokens provide more granular control and are GitHub's recommended approach:

1. Go to [GitHub Settings](https://github.com/settings/profile)
2. Click **Developer settings** (bottom of left sidebar)
3. Click **Personal access tokens** → **Fine-grained tokens**
4. Click **Generate new token**
5. Configure the token:
   - **Token name**: e.g., "Django Issue Capture"
   - **Expiration**: Choose based on your security requirements
   - **Repository access**: Select "Only select repositories" and choose the target repo(s)
   - **Permissions**: Under "Repository permissions", set:
     - **Issues**: Read and write (required to create issues)
     - **Metadata**: Read-only (automatically selected)
6. Click **Generate token**
7. Copy the token immediately (it won't be shown again)

**Option 2: Classic token**

Classic tokens are simpler but have broader access:

1. Go to [GitHub Settings](https://github.com/settings/profile)
2. Click **Developer settings** (bottom of left sidebar)
3. Click **Personal access tokens** → **Tokens (classic)**
4. Click **Generate new token** → **Generate new token (classic)**
5. Configure the token:
   - **Note**: e.g., "Django Issue Capture"
   - **Expiration**: Choose based on your security requirements
   - **Scopes**: Select `repo` (grants full control of private repositories, including issues)
6. Click **Generate token**
7. Copy the token immediately (it won't be shown again)

#### Required Permissions

| Permission | Type | Purpose |
|------------|------|---------|
| Issues | Read and write | Create and manage issues in the repository |
| Metadata | Read-only | Access repository metadata (auto-included) |

> **Note**: Classic tokens with `repo` scope grant broader access than needed. For production use, fine-grained tokens with minimal permissions are recommended.

#### Adding the Token to Django

1. Navigate to Django Admin → **Issue Capture Settings**
2. Enter your GitHub repository in the format `owner/repo` (e.g., `octocat/hello-world`)
3. Paste your Personal Access Token in the **GitHub API key** field
4. Save the settings

### Environment Variables (Production)

For production, use environment variables:

```python
# settings.py
from django.conf import settings

# Override singleton defaults with env vars
ISSUE_CAPTURE_LLM_API_KEY = os.getenv("ISSUE_CAPTURE_LLM_API_KEY")
ISSUE_CAPTURE_GITHUB_API_KEY = os.getenv("GITHUB_API_KEY")
```

## Usage

### Create Issue via UI

1. Navigate to `/issues/create/`
2. Choose creation mode:
   - **Standard Form**: Manual entry with all fields
   - **AI Quick Generate**: One-shot AI enhancement from basic input

### Promote to GitHub

1. View issues at `/issues/list/`
2. Click issue to view details
3. Click "Promote to GitHub" (or use admin interface)

### Admin Interface

The Django admin provides:
- Issue management with status tracking
- One-click GitHub promotion (HTMX-powered)
- Template configuration

## Development

```bash
# Clone and install
git clone https://github.com/directory-platform/django-issue-capture
cd django-issue-capture
uv sync --extra dev

# Run tests
PYTHONPATH=. uv run python tests/manage.py test

# Run quality checks
ruff check src/ tests/
ruff format src/ tests/
mypy src/
```

## Dependencies

- Django ≥ 4.2
- django-solo ≥ 2.0
- shortuuid ≥ 1.0
- requests ≥ 2.32
- litellm ≥ 1.70
- django-markdownify ≥ 0.9

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Releasing

See [RELEASING.md](./RELEASING.md) for instructions on publishing new versions to PyPI.

## Support

- **Issues**: https://github.com/directory-platform/django-issue-capture/issues
- **Docs**: https://github.com/directory-platform/django-issue-capture

## Credits

Part of the Directory Platform ecosystem. Extracted from [directory-builder](https://github.com/heysamtexas/directory-builder).
