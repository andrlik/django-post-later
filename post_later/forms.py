from django import forms
from django.utils.translation import gettext_lazy as _


class LinkMastodonAccountForm(forms.Form):

    instance_url = forms.fields.URLField(
        label=_("Server URL"),
        help_text=_("Include the full domain, e.g. https://mastodon.social"),
    )
