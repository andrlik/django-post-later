from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from .models.social_accounts import Account


class LinkMastodonAccountForm(forms.Form):
    """
    Custom form that we use to collect the remote instance domain.
    """

    instance_url = forms.fields.URLField(
        label=_("Server URL"),
        help_text=_("Include the full domain, e.g. https://mastodon.social"),
    )


class AccountCreateForm(forms.Form):
    """
    Custom form that we use to start account linking process.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        account_choices = []
        for allowed_account_type in settings.ENABLED_ACCOUNT_TYPES:
            try:
                enum_value = getattr(Account.AccountType, allowed_account_type)
                account_choices.append((enum_value.value, enum_value.label))
            except KeyError:  # pragma: nocover
                pass
        self.fields["account_type"].choices = account_choices  # type: ignore

    account_type = forms.ChoiceField(
        choices=[],
        help_text=_("Type of account you wish to link."),
        label=_("Account Type"),
    )
