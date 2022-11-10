from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel
from rules.contrib.models import RulesModelBase, RulesModelMixin

# Put your models here.


class MastodonInstanceClient(
    RulesModelMixin, TimeStampedModel, models.Model, metaclass=RulesModelBase
):
    """
    Represents a single mastodon instance with it's client credentials
    and base api url.
    """

    api_base_url = models.URLField(
        unique=True,
        help_text=_("Unique url for instance, e.g. https://mastodon.social"),
    )
    client_id = models.CharField(
        "Client Id", max_length=100, help_text=_("Unique client id for instance.")
    )
    client_secret = models.CharField(
        "Client Secret",
        max_length=100,
        help_text=_("Client secret token for instance."),
    )
    vapid_key = models.CharField(
        "Vapid Key",
        max_length=250,
        blank=True,
        null=True,
        help_text=_(
            "Optional. Vapid key for use in receiving push notifications is server supports it."
        ),
    )

    def __str__(self):  # pragma: nocover
        return f"{self.api_base_url}-Key:({self.client_id})"


def mastodon_account_directory_path(instance, filename):
    return f"avatars/mastodon/account_{instance.user_account.id}/{filename}"


class MastodonAvatar(
    RulesModelMixin, TimeStampedModel, models.Model, metaclass=RulesModelBase
):
    source_url = models.URLField(
        null=True, blank=True, help_text=_("Original URL from mastodon instance.")
    )
    cached_avatar = models.ImageField(
        null=True,
        blank=True,
        upload_to=mastodon_account_directory_path,
        help_text=_("Locally cached version of avatar."),
    )
    cache_stale = models.BooleanField(
        default=True,
        help_text=_("Should we refresh the cached image at next opportunity?"),
    )
    user_account = models.OneToOneField("MastodonUserAuth", on_delete=models.CASCADE)

    def __str__(self):  # pragma: nocover
        return f"{self.user_account.account_username} - {self.id} - Stale: {self.cache_stale}"


class MastodonUserAuth(
    RulesModelMixin, TimeStampedModel, models.Model, metaclass=RulesModelBase
):
    """
    A user's authentication for given Mastodon account.
    """

    instance_client = models.ForeignKey(
        MastodonInstanceClient, on_delete=models.CASCADE
    )
    account_username = models.CharField(max_length=100, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    user_oauth_key = models.CharField(
        max_length=250, null=True, blank=True, help_text=_("Users OAuth code.")
    )
    user_auth_token = models.CharField(
        max_length=250,
        null=True,
        blank=True,
        help_text=_("Current auth token for user session."),
    )

    @property
    def is_ready_post(self) -> bool:
        """
        Returns whether this has all the values needed to post.
        """
        if (
            self.account_username is not None
            and self.user_oauth_key is not None
            and self.user_auth_token is not None
        ):
            return True
        return False

    def __str__(self):  # pragma: nocover
        return f"{self.user} - @{self.account_username}@{self.instance_client.api_base_url[8:]}"
