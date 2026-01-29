"""
Test the new comprehensive generation views.
"""

from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from django_issue_capture.models import IssueCaptureSettings


class ComprehensiveViewTest(TestCase):
    """Test views for comprehensive issue generation."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="staffuser", email="staff@example.com", password="testpass123", is_staff=True
        )
        self.client = Client()
        self.client.login(username="staffuser", password="testpass123")

        # Configure LLM settings
        settings = IssueCaptureSettings.get_solo()
        settings.show_ai_interface = True
        settings.llm_api_key = "test-key-123"
        settings.llm_model = "gpt-4o-mini"
        settings.save()

    @patch("django_issue_capture.llm_service.completion")
    def test_generate_comprehensive_issue_preview(self, mock_completion):
        """Test that comprehensive generation returns preview."""
        # Mock completion function
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = """
        # Enhanced Issue Title

        ## Description
        Comprehensive description with detailed steps and context

        ## Acceptance Criteria
        - Should work correctly when implemented

        ## Technical Specifications
        Use Django best practices

        ## Implementation Hints
        Follow existing patterns

        ## Metadata
        Priority: high
        Complexity: medium
        Labels: bug,enhancement
        Confidence: 0.9
        """
        mock_completion.return_value = mock_response

        response = self.client.post(
            reverse("django_issue_capture:generate_comprehensive"),
            {"title": "Test Issue", "description": "Something is broken", "template": "bug", "action": "preview"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enhanced Issue Title")

    def test_staff_permissions_required(self):
        """Test that non-staff users can't access generation."""
        _regular_user = User.objects.create_user(
            username="regular", email="regular@example.com", password="testpass123"
        )

        self.client.logout()
        self.client.login(username="regular", password="testpass123")

        response = self.client.post(
            reverse("django_issue_capture:generate_comprehensive"), {"description": "Test issue"}
        )
        self.assertEqual(response.status_code, 403)

    def test_empty_description_rejected(self):
        """Test that empty description is rejected."""
        response = self.client.post(
            reverse("django_issue_capture:generate_comprehensive"),
            {
                "title": "Test",
                "description": "",  # Empty description
                "template": "bug",
            },
        )

        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertIn("error", response_data)
        self.assertIn("required", response_data["error"])
