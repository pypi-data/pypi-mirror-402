"""Demo views for django-issue-capture testing."""

from django.shortcuts import render


def demo(request):
    """Demo page showing the floating issue button."""
    return render(request, "demo.html")
