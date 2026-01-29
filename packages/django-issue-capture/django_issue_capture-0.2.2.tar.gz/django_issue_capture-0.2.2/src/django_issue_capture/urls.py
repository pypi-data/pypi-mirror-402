from django.urls import path

from . import views

app_name = "django_issue_capture"

urlpatterns = [
    # Specific patterns first
    path("create/", views.create_issue, name="create"),
    path("list/", views.issue_list, name="list"),
    # AI-powered issue generation
    path("generate/", views.generate_comprehensive_issue, name="generate_comprehensive"),
    path("enhance/", views.quick_enhance_issue, name="quick_enhance"),  # Legacy redirect
    # Catch-all pattern LAST (so it doesn't intercept other patterns)
    path("<str:short_uuid>/", views.issue_detail, name="detail"),
]
