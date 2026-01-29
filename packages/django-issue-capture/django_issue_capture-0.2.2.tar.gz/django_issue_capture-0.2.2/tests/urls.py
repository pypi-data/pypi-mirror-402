"""Test URLs for django-issue-capture."""

from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    path("", views.demo, name="demo"),
    path("admin/", admin.site.urls),
    path("issues/", include("django_issue_capture.urls")),
]
