# Django Forge Issues

Create github/gitlab issues directly from a Django application.

## Installation

`pip install django-forge-issues[gitlab]` or `pip install django-forge-issues[github]`

Then add `DJANGO_FORGE_ISSUES` to your `INSTALLED_APPS` and to your `urls.py`:
```
urlpatterns += [path("", include("django_forge_issues.urls"))]
```
This give you the urls `django_forge_issues/create/<str:contenttype>/<int:pk>`
and `django_forge_issues/list/<str:contenttype>/<int:pk>` for creating resp.
listing the urls.

## Configuration

```python
DJANGO_FORGE_ISSUES_PROJECT = "https://the.url.of/your/project"
DJANGO_FORGE_ISSUES_TOKEN = "secret-token"
```
For Gitlab projects, create the token in Project Settings -> Access tokens. Add a
token that has the role `Reporter` and the `api` scope.

For Github projects, the token can be anything that can be used for
authentication as described in [the authentication examples of
pygithub](https://pygithub.readthedocs.io/en/stable/examples/Authentication.html).
So for example:
```
from github import Auth
DJANGO_FORGE_ISSUES_TOKEN = Auth("secret-token")
```
