from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from django_issue_capture.models import Issue, IssueCaptureSettings


class IssueModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="testpass123")
        self.staff_user = User.objects.create_user(
            username="staffuser", email="staff@example.com", password="staffpass123", is_staff=True
        )

    def test_issue_creation(self):
        """Test basic issue creation"""
        issue = Issue.objects.create(
            title="Test Issue",
            description="Test description",
            reported_url="https://example.com",
            reported_by=self.user,
        )

        self.assertEqual(issue.title, "Test Issue")
        self.assertEqual(issue.status, "open")
        self.assertEqual(issue.priority, "medium")
        self.assertIsNotNone(issue.short_uuid)

    def test_issue_str_representation(self):
        """Test string representation of issue"""
        issue = Issue.objects.create(title="Test Issue", description="Test description", reported_by=self.user)

        expected = f"#{issue.short_uuid}: Test Issue"
        self.assertEqual(str(issue), expected)


class IssueViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="testpass123")
        self.staff_user = User.objects.create_user(
            username="staffuser", email="staff@example.com", password="staffpass123", is_staff=True
        )
        self.issue = Issue.objects.create(
            title="Test Issue", description="Test description", reported_by=self.staff_user
        )

    def test_create_issue_get_requires_staff(self):
        """Test that create issue form requires staff permissions"""
        # Regular user should get 403
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("django_issue_capture:create"))
        self.assertEqual(response.status_code, 403)

        # Staff user should get form
        self.client.login(username="staffuser", password="staffpass123")
        response = self.client.get(reverse("django_issue_capture:create"))
        self.assertEqual(response.status_code, 200)

    def test_create_issue_post_success(self):
        """Test successful issue creation"""
        self.client.login(username="staffuser", password="staffpass123")

        response = self.client.post(
            reverse("django_issue_capture:create"),
            {
                "title": "New Test Issue",
                "description": "New test description",
                "priority": "high",
                "reported_url": "https://example.com/test",
            },
        )

        self.assertEqual(response.status_code, 200)

        # Check that issue was created
        issue = Issue.objects.filter(title="New Test Issue").first()
        self.assertIsNotNone(issue)
        self.assertEqual(issue.priority, "high")
        self.assertEqual(issue.reported_by, self.staff_user)

    def test_issue_detail_requires_staff(self):
        """Test that issue detail requires staff permissions"""
        # Regular user should get 403
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("django_issue_capture:detail", kwargs={"short_uuid": self.issue.short_uuid}))
        self.assertEqual(response.status_code, 403)

        # Staff user should get detail
        self.client.login(username="staffuser", password="staffpass123")
        response = self.client.get(reverse("django_issue_capture:detail", kwargs={"short_uuid": self.issue.short_uuid}))
        self.assertEqual(response.status_code, 200)

    def test_issue_list_requires_staff(self):
        """Test that issue list requires staff permissions"""
        # Regular user should get 403
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("django_issue_capture:list"))
        self.assertEqual(response.status_code, 403)

        # Staff user should get list
        self.client.login(username="staffuser", password="staffpass123")
        response = self.client.get(reverse("django_issue_capture:list"))
        self.assertEqual(response.status_code, 200)


class IssueCaptureSettingsValidationTest(TestCase):
    """Tests for IssueCaptureSettings validation"""

    def test_github_token_accepts_classic_token(self):
        """Test that classic ghp_ tokens are accepted"""
        settings = IssueCaptureSettings.get_solo()
        settings.github_repo = "owner/repo"
        settings.github_api_key = "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        settings.full_clean()  # Should not raise

    def test_github_token_accepts_fine_grained_token(self):
        """Test that fine-grained github_pat_ tokens are accepted"""
        settings = IssueCaptureSettings.get_solo()
        settings.github_repo = "owner/repo"
        settings.github_api_key = "github_pat_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        settings.full_clean()  # Should not raise

    def test_github_token_rejects_invalid_prefix(self):
        """Test that tokens with invalid prefixes are rejected"""
        settings = IssueCaptureSettings.get_solo()
        settings.github_repo = "owner/repo"
        settings.github_api_key = "invalid_token_xxxxxxxxxxxxxxx"
        with self.assertRaises(ValidationError) as ctx:
            settings.full_clean()
        self.assertIn("github_api_key", ctx.exception.message_dict)
