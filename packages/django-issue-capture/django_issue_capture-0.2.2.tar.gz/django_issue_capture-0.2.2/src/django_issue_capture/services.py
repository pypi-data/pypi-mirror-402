import logging

import requests
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from .models import Issue, IssueCaptureSettings

logger = logging.getLogger(__name__)

# HTTP status codes
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404


class GitHubError(Exception):
    """Custom exception for GitHub API errors."""


class GitHubService:
    """Service class for GitHub API integration."""

    def __init__(self):
        self.settings = IssueCaptureSettings.get_solo()
        self.base_url = "https://api.github.com"

    def _get_headers(self) -> dict[str, str]:
        """Get headers for GitHub API requests."""
        if not self.settings.github_api_key:
            raise GitHubError("GitHub API key not configured")

        return {
            "Authorization": f"token {self.settings.github_api_key}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
        }

    def _validate_settings(self) -> None:
        """Validate GitHub settings before making API calls."""
        if not self.settings.github_repo:
            raise GitHubError("GitHub repository not configured")

        if not self.settings.github_api_key:
            raise GitHubError("GitHub API key not configured")

        if "/" not in self.settings.github_repo:
            raise GitHubError("Invalid GitHub repository format. Expected: owner/repo")

    def _format_issue_body(self, issue: Issue) -> str:
        """Format the issue description for GitHub."""
        body_parts = [
            issue.description,
            "",
            "---",
            f"**Original URL**: {issue.reported_url}",
            f"**Reported by**: {issue.reported_by.username}",
            f"**Priority**: {issue.get_priority_display()}",
            f"**Status**: {issue.get_status_display()}",
            f"**Created**: {issue.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        ]

        if issue.assigned_to:
            body_parts.insert(-1, f"**Assigned to**: {issue.assigned_to.username}")

        return "\n".join(body_parts)

    def create_github_issue(self, issue: Issue, promoted_by: User) -> tuple[str, int]:  # noqa: C901 - GitHub API integration requires error handling
        """Create a GitHub issue from a local Issue instance.

        Returns:
            Tuple of (github_url, issue_number)

        Raises:
            GitHubError: If GitHub API call fails

        """
        self._validate_settings()

        # Prepare the issue data
        issue_data = {
            "title": issue.title,
            "body": self._format_issue_body(issue),
            "labels": [self.settings.github_label] if self.settings.github_label else [],
        }

        # Make the API request
        url = f"{self.base_url}/repos/{self.settings.github_repo}/issues"

        try:
            response = requests.post(url, headers=self._get_headers(), json=issue_data, timeout=30)

            if response.status_code == HTTP_CREATED:
                github_issue = response.json()
                github_url = github_issue["html_url"]
                issue_number = github_issue["number"]

                logger.info("Successfully created GitHub issue #%s for local issue #%s", issue_number, issue.short_uuid)

                return github_url, issue_number

            if response.status_code == HTTP_UNAUTHORIZED:
                raise GitHubError("GitHub API authentication failed. Check your API key.")

            if response.status_code == HTTP_FORBIDDEN:
                if "rate limit" in response.text.lower():
                    raise GitHubError("GitHub API rate limit exceeded. Please try again later.")
                raise GitHubError("GitHub API access forbidden. Check repository permissions.")

            if response.status_code == HTTP_NOT_FOUND:
                raise GitHubError(f"GitHub repository '{self.settings.github_repo}' not found.")

            error_msg = f"GitHub API error: {response.status_code}"
            try:
                error_data = response.json()
                if "message" in error_data:
                    error_msg += f" - {error_data['message']}"
            except (ValueError, KeyError):
                error_msg += f" - {response.text[:200]}"

            raise GitHubError(error_msg)

        except requests.exceptions.Timeout:
            raise GitHubError("GitHub API request timed out. Please try again.") from None

        except requests.exceptions.ConnectionError:
            raise GitHubError("Failed to connect to GitHub API. Please check your internet connection.") from None

        except requests.exceptions.RequestException as e:
            raise GitHubError(f"GitHub API request failed: {e!s}") from e

    @transaction.atomic
    def promote_issue(self, issue: Issue, promoted_by: User) -> bool:
        """Promote a local issue to GitHub and update the database.

        Returns:
            True if successful, False otherwise

        Raises:
            GitHubError: If promotion fails

        """
        if issue.is_promoted_to_github:
            raise GitHubError("Issue has already been promoted to GitHub")

        # Create the GitHub issue
        github_url, issue_number = self.create_github_issue(issue, promoted_by)

        # Update the local issue record
        issue.github_url = github_url
        issue.github_issue_number = issue_number
        issue.github_promoted_at = timezone.now()
        issue.github_promoted_by = promoted_by
        issue.save()

        logger.info("Issue #%s promoted to GitHub #%s by %s", issue.short_uuid, issue_number, promoted_by.username)

        return True

    def test_connection(self) -> tuple[bool, str]:
        """Test the GitHub API connection and permissions.

        Returns:
            Tuple of (success, message)

        """
        try:
            self._validate_settings()

            # Test with a simple API call to get repository info
            url = f"{self.base_url}/repos/{self.settings.github_repo}"
            response = requests.get(url, headers=self._get_headers(), timeout=10)

            if response.status_code == HTTP_OK:
                repo_data = response.json()
                return True, f"Successfully connected to {repo_data['full_name']}"

            if response.status_code == HTTP_UNAUTHORIZED:
                return False, "Authentication failed. Check your API key."

            if response.status_code == HTTP_NOT_FOUND:
                return False, f"Repository '{self.settings.github_repo}' not found."

            return False, f"API error: {response.status_code}"

        except Exception as e:
            return False, f"Connection test failed: {e!s}"
