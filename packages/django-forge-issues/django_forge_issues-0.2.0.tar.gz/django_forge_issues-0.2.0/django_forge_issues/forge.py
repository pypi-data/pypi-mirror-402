import urllib
from dataclasses import dataclass
from typing import Optional, Self

import httpx
from django.conf import settings


@dataclass
class Issue:
    title: str
    body: Optional[str]
    labels: [str]
    url: str

    @classmethod
    def from_issue(cls, issue: dict) -> Self:
        title = issue["title"]
        body = issue.get("body", issue.get("description", ""))
        labels = issue["labels"]
        url = issue.get("html_url", issue.get("web_url", ""))
        return cls(title, body, labels, url)


class ForgeWrapper:
    headers = {}
    endpoint = ""

    def __init__(self):
        project = getattr(settings, "DJANGO_FORGE_ISSUES_PROJECT", "")
        token = getattr(settings, "DJANGO_FORGE_ISSUES_TOKEN")
        p_project = urllib.parse.urlparse(project)
        server = f"{p_project.scheme}://{p_project.hostname}"
        project = p_project.path[1:]
        if server == "https://github.com":
            self.headers = {
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
            }
            self.endpoint = f"https://api.github.com/repos/{project}/issues"
        else:
            self.headers = {"PRIVATE-TOKEN": token}
            self.endpoint = f"{server}/api/v4/projects/{p_project.path}/issues"

    @property
    def github(self):
        return self.endpoint.startswith("https://api.github.com")

    def get_issues(self, labels=[]) -> list[Issue]:
        labels = [str(label) for label in labels] + ["django_forge_issues"]
        issues = []
        params = {"labels": labels}
        r = httpx.get(self.endpoint, params=params, headers=self.headers)
        if r:
            return [Issue.from_issue(issue) for issue in r.json()]
        return issues

    def create_issue(self, title: str, body: str = "", labels: [str] = []) -> bool:
        labels = [str(label) for label in labels] + ["django_forge_issues"]
        data = {"title": title, "description": body, "labels": labels}
        if self.github:
            data = {"title": title, "body": body, "labels": labels}
        r = httpx.post(self.endpoint, json=data, headers=self.headers)
        r.raise_for_status()
