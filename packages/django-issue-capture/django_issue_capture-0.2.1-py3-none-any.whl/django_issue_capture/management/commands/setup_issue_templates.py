from django.core.management.base import BaseCommand

from django_issue_capture.models import IssueTemplate


class Command(BaseCommand):
    help = "Set up default issue templates for AI-powered issue generation"

    def handle(self, *args, **options):
        templates_data = [
            {
                "name": "bug",
                "display_name": "Bug Report",
                "description": "Report a software bug or defect",
                "required_context": [
                    "problem_description",
                    "steps_to_reproduce",
                    "expected_behavior",
                    "actual_behavior",
                    "environment",
                    "frequency",
                ],
                "generation_prompt": """
                You are creating a comprehensive bug report that will be used by developers and coding agents.

                Structure the bug report with:
                - Clear, descriptive title that summarizes the issue
                - Detailed description of the problem
                - Step-by-step reproduction instructions
                - Expected vs actual behavior
                - Environment details (browser, device, etc.)
                - Error messages or logs if mentioned
                - Acceptance criteria for the fix
                - Technical implementation hints

                Make it actionable and complete so developers can understand, reproduce, and fix the issue.
                """,
                "default_labels": "bug",
            },
            {
                "name": "feature",
                "display_name": "Feature Request",
                "description": "Request a new feature or enhancement",
                "required_context": [
                    "feature_description",
                    "problem_solved",
                    "user_benefit",
                    "expected_behavior",
                    "use_cases",
                ],
                "generation_prompt": """
                You are creating a comprehensive feature request that will be used by developers and product managers.

                Structure the feature request with:
                - Clear, descriptive title
                - Problem statement (what problem this solves)
                - User story format (As a [user], I want [feature] so that [benefit])
                - Detailed description of how the feature should work
                - Acceptance criteria (testable criteria for completion)
                - Use cases and examples
                - Priority justification
                - Technical implementation hints

                Make it actionable and complete for development teams.
                """,
                "default_labels": "feature,enhancement",
            },
            {
                "name": "task",
                "display_name": "Task",
                "description": "General task or work item",
                "required_context": ["task_description", "deliverables", "completion_criteria", "dependencies"],
                "generation_prompt": """
                You are creating a well-defined task that will be used by developers and project managers.

                Structure the task with:
                - Clear, descriptive title
                - Task overview (what needs to be accomplished)
                - Specific deliverables
                - Acceptance criteria (how to know when complete)
                - Dependencies or prerequisites
                - Technical requirements or constraints
                - Definition of done

                Make it actionable and unambiguous.
                """,
                "default_labels": "task",
            },
            {
                "name": "enhancement",
                "display_name": "Enhancement",
                "description": "Improvement to existing functionality",
                "required_context": [
                    "current_functionality",
                    "proposed_improvements",
                    "problems_addressed",
                    "user_benefit",
                ],
                "generation_prompt": """
                You are creating a comprehensive enhancement request that will be used by developers.

                Structure the enhancement with:
                - Clear, descriptive title
                - Current state (existing functionality and its limitations)
                - Proposed enhancement (specific improvements)
                - Benefits (how this improves user experience)
                - Implementation considerations
                - Acceptance criteria
                - Impact assessment on existing functionality

                Make it clear and actionable for development.
                """,
                "default_labels": "enhancement",
            },
        ]

        created_count = 0
        updated_count = 0

        for template_data in templates_data:
            template, created = IssueTemplate.objects.update_or_create(
                name=template_data["name"], defaults=template_data
            )

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created template: {template.display_name}"))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f"Updated template: {template.display_name}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"\nSetup complete! Created {created_count} new templates, updated {updated_count} existing templates."
            )
        )

        if created_count > 0 or updated_count > 0:
            self.stdout.write("You can now use AI-powered issue generation with these templates.")
