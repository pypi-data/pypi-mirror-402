"""
Tests for the simplified single-shot comprehensive issue generation.
No more conversation complexity - just direct issue generation.
"""

from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.test import TestCase

from django_issue_capture.llm_service import IssueLLMService
from django_issue_capture.models import Issue, IssueCaptureSettings, IssueTemplate


class ComprehensiveGenerationTest(TestCase):
    """Test the new single-shot comprehensive generation approach."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="testpass123")

        # Configure LLM settings
        settings = IssueCaptureSettings.get_solo()
        settings.show_ai_interface = True
        settings.llm_api_key = "test-key-123"
        settings.llm_model = "gpt-4o-mini"
        settings.save()

        self.template = IssueTemplate.objects.create(
            name="bug",
            display_name="Bug Report",
            description="Bug reporting template",
            generation_prompt="Generate a comprehensive bug report",
        )

    @patch("django_issue_capture.llm_service.completion")
    def test_comprehensive_generation_works(self, mock_completion):
        """Test that comprehensive generation creates markdown content."""
        # Mock litellm response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = """# Enhanced Bug Report: Login Issue

## Description
User cannot login to system due to authentication failure.

## Acceptance Criteria
- [ ] Users should be able to login successfully
- [ ] Error messages should be clear

## Technical Specifications
Check authentication service configuration.

## Implementation Hints
Review login validation logic in auth module.

## Metadata
Priority: high
Complexity: medium
Labels: bug, authentication
Confidence: 0.9
"""
        mock_completion.return_value = mock_response

        service = IssueLLMService()
        result = service.generate_comprehensive_issue(
            title="Login broken", description="User can't login to the system", template_name="bug", user=self.user
        )

        # Verify simplified markdown data is generated
        self.assertEqual(result["title"], "Login broken")  # Original title preserved
        self.assertIn("Enhanced Bug Report", result["description"])
        self.assertIn("## Description", result["description"])
        self.assertIn("## Acceptance Criteria", result["description"])
        self.assertEqual(result["template_name"], "bug")

    @patch("django_issue_capture.llm_service.completion")
    def test_ride_or_die_when_llm_fails(self, mock_completion):
        """Test 'ride or die' behavior - when LLM fails, we fail hard."""
        mock_completion.side_effect = Exception("LLM API Error")

        service = IssueLLMService()

        # Should raise exception, no fallback
        with self.assertRaises(Exception) as context:
            service.generate_comprehensive_issue(
                title="Login broken", description="User can't login", template_name="bug", user=self.user
            )

        # Verify the exception message
        self.assertIn("LLM generation failed", str(context.exception))

    def test_issue_creation_from_generated_data(self):
        """Test creating Issue objects from simplified markdown data."""
        generated_data = {
            "title": "Test Issue",
            "description": """# Test Issue

## Description
This is a comprehensive test issue with markdown formatting.

## Acceptance Criteria
- [ ] Should work correctly
- [ ] Should be well tested

## Technical Specifications
Use standard patterns and follow best practices.

## Implementation Hints
Follow existing code style in the repository.""",
            "template_name": "bug",
        }

        service = IssueLLMService()
        issue = service.create_issue_from_generated_data(
            generated_data=generated_data, user=self.user, reported_url="https://example.com"
        )

        # Verify issue was created correctly with markdown
        self.assertIsInstance(issue, Issue)
        self.assertEqual(issue.title, "Test Issue")
        self.assertEqual(issue.creation_mode, "ai_generated")
        self.assertEqual(issue.llm_confidence_score, 0.8)  # Default value
        self.assertIn("## Description", issue.description)
        self.assertIn("## Acceptance Criteria", issue.description)

    @patch("django_issue_capture.llm_service.completion")
    def test_minimal_input_works(self, mock_completion):
        """Test that minimal input still produces usable output."""
        # Mock minimal but valid markdown response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = """# Simple Issue

## Description
Something appears to be broken in the system.

## Basic Fix
Check the system logs for errors."""
        mock_completion.return_value = mock_response

        service = IssueLLMService()
        result = service.generate_comprehensive_issue(
            title="",  # Empty title
            description="Something is broken",
            user=self.user,
        )

        # Should still work with minimal input and extract title from markdown
        self.assertEqual(result["title"], "Simple Issue")  # Extracted from # heading
        self.assertIn("Simple Issue", result["description"])
        self.assertIn("## Description", result["description"])
