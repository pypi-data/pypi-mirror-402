import urllib
from dataclasses import dataclass
from typing import Optional

from django.conf import settings


@dataclass
class Issue:
    title: str
    body: Optional[str]
    labels: [str]
    url: str


class ForgeWrapper:
    github = None
    gitlab = None

    def __init__(self):
        project = getattr(settings, "DJANGO_FORGE_ISSUES_PROJECT", "")
        token = getattr(settings, "DJANGO_FORGE_ISSUES_TOKEN")
        p_project = urllib.parse.urlparse(project)
        server = f"{p_project.scheme}://{p_project.hostname}"
        project = p_project.path[1:]
        if server == "https://github.com":
            from github import Github

            g = Github(auth=token)
            self.github = g.get_repo(project)
        else:
            import gitlab

            gl = gitlab.Gitlab(server, oauth_token=token)
            self.gitlab = gl.projects.get(project)

    def get_issues(self, labels=[]) -> list[Issue]:
        labels = [str(label) for label in labels] + ["django_forge_issues"]
        issues = []
        if self.github:
            for issue in self.github.get_issues(state="open"):
                if set(labels).issubset([label.name for label in issue.labels]):
                    issues.append(
                        Issue(issue.title, issue.body, issue.labels, issue.html_url)
                    )
        if self.gitlab:
            for issue in self.gitlab.issues.list(get_all=True, state="opened"):
                if set(labels).issubset(issue.labels):
                    issues.append(
                        Issue(issue.title, issue.description, issue.labels, "")
                    )
        return issues

    def create_issue(self, title: str, body: str = "", labels: [str] = []) -> bool:
        labels = [str(label) for label in labels] + ["django_forge_issues"]
        if self.github:
            self.github.create_issue(title=title, body=body, labels=labels)
        if self.gitlab:
            self.gitlab.issues.create(
                {"title": title, "description": body, "labels": labels}
            )
