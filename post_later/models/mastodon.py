from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel
from rules.contrib.models import RulesModel

from ..rules import is_mastodon_user, is_valid_user

# Put your models here.


class MastodonInstanceClient(TimeStampedModel, RulesModel):
    """
    Represents a single mastodon instance with it's client credentials
    and base api url.

    Attributes:
        api_base_url (str): The base URL for the Mastodon instance. We create a unique client for each URL.
        client_id (str | None): The client_id given to us by the remote instance.
        client_secret (str | None): The client secret given to us by the remote instance.
        vapid_key (str | None): The streaming key returned by the instance.
    """

    api_base_url = models.URLField(
        unique=True,
        help_text=_("Unique url for instance, e.g. https://mastodon.social"),
    )
    client_id = models.CharField(
        "Client Id",
        max_length=100,
        help_text=_("Unique client id for instance."),
        null=True,
        blank=True,
    )
    client_secret = models.CharField(
        "Client Secret",
        max_length=100,
        help_text=_("Client secret token for instance."),
        null=True,
        blank=True,
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

    @property
    def ready(self) -> bool:
        """Returns a bool indicating whether the client id and secret are ready for use."""
        if self.client_id is not None and self.client_secret is not None:
            return True
        return False

    def __str__(self):  # pragma: nocover
        return f"{self.api_base_url}-Key:({self.client_id})"


def mastodon_account_directory_path(instance, filename):
    return f"avatars/mastodon/account_{instance.user_account.id}/{filename}"


class MastodonAvatar(TimeStampedModel, RulesModel):
    """
    Represents the avatar associated with a given Mastodon account.

    Attributes:
        source_url (str): The URL of the static avatar image on the remote instance.
        cached_avatar (file | None): Our locally cached version of the remote image. Fetched asyncronously.
        cache_stale (bool): Indicates if the cache is stale and needs to be refreshed from remote instance.
        user_account (MastodonUserAuth): OneToOne relationship to MastodonUserAuth.
    """

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


class MastodonUserAuth(TimeStampedModel, RulesModel):
    """
    A user's authentication for given Mastodon account. Only the associated user can see, edit,
    or delete this object.

    Attributes:
        instance_client (MastodonInstanceClient): Foreign key to our defined app for a given instance.
        account_username (str | None): The username for the account. Fetched from instance.
        user (User): Foreign key to the `AUTH_USER_MODEL`.
        user_oauth_key (str | None): The oauth user key given by the instance.
        user_auth_token (str | None): The auth token used for credentially on all subsequent user requests.
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
        Returns a bool representing whether this has all the values needed to post.
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

    class Meta:
        rules_permissions = {
            "add": is_valid_user,
            "read": is_mastodon_user,
            "edit": is_mastodon_user,
            "delete": is_mastodon_user,
            "list": is_valid_user,
        }
