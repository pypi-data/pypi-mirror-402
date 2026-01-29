from django import forms


class IssueForm(forms.Form):
    body = forms.CharField(widget=forms.Textarea)

    class Media:
        css = {"all": ["django_forge_issues.css"]}
