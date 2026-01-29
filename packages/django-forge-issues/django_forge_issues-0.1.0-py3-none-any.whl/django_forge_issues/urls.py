from django.urls import path

from django_forge_issues.views import CreateIssue, ListIssues

urlpatterns = [
    path(
        "django_forge_issues/create/<str:contenttype>/<int:pk>",
        CreateIssue.as_view(),
        name="create-issue",
    ),
    path(
        "django_forge_issues/list/<str:contenttype>/<int:pk>",
        ListIssues.as_view(),
        name="list-issues",
    ),
]
