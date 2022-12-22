from django import forms
from django.utils.translation import gettext_lazy as _


class LinkMastodonAccountForm(forms.Form):
    """
    Custom form that we use to collect the remote instance domain.
    """

    instance_url = forms.fields.URLField(
        label=_("Server URL"),
        help_text=_("Include the full domain, e.g. https://mastodon.social"),
    )
