from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from django_forge_issues.forge import ForgeWrapper
from django_forge_issues.forms import IssueForm


class DjangoForgeIsssuesMixin:
    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        app_label, model = kwargs["contenttype"].split(".")
        contenttype = get_object_or_404(ContentType, app_label=app_label, model=model)
        self.object = get_object_or_404(contenttype.model_class(), pk=kwargs.get("pk"))
        self.labels = [
            self.kwargs["contenttype"],
            self.kwargs["pk"],
            f"user:{self.request.user}",
        ]


class CreateIssue(DjangoForgeIsssuesMixin, LoginRequiredMixin, FormView):
    form_class = IssueForm
    template_name = "django_forge_issues/create_issue.html"

    def form_valid(self, form):
        url = self.request.build_absolute_uri(self.object.get_absolute_url())

        title = f"Issue created on {url}"
        body = render_to_string(
            "django_forge_issues/issue_body.html",
            {
                "request": self.request,
                "url": url,
                "object": self.object,
                "body": form.cleaned_data["body"],
            },
        )
        try:
            fw = ForgeWrapper()
            fw.create_issue(title=title, body=body, labels=self.labels)
            messages.add_message(
                self.request, messages.INFO, _("Issue was created, thank you!")
            )
        except Exception:
            form.add_error(None, _("Issue could not be created, please try again"))
            return self.form_invalid(form)
        return redirect(
            "create-issue", contenttype=self.kwargs["contenttype"], pk=self.kwargs["pk"]
        )


class ListIssues(DjangoForgeIsssuesMixin, LoginRequiredMixin, TemplateView):
    template_name = "django_forge_issues/list_issues.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["issues"] = ForgeWrapper().get_issues(labels=self.labels)
        return context
