from __future__ import annotations

import uuid
from io import BytesIO

import httpx
from asgiref.sync import async_to_sync
from django.core.files import File
from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel
from rules.contrib.models import RulesModel

from ..rules import is_mastodon_avatar_owner, is_owner, is_valid_user
from .abstract import OwnedModel, RemoteUserAuthModel
from .social_accounts import Account

# Put your models here.


class MastodonInstanceClient(TimeStampedModel, models.Model):
    """
    Represents a single mastodon instance with it's client credentials
    and base api url.

    Attributes:
        id (uuid): Primary key for the client.
        api_base_url (str): The base URL for the Mastodon instance. We create a unique client for each URL.
        client_id (str | None): The client_id given to us by the remote instance.
        client_secret (str | None): The client secret given to us by the remote instance.
        vapid_key (str | None): The streaming key returned by the instance.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
    """
    Returns the directory path for saving a user upload for a mastodon account.
    """

    return f"avatars/mastodon/account_{instance.user_account.id}/{filename}"


class MastodonAvatar(TimeStampedModel, RulesModel):
    """
    Represents the avatar associated with a given Mastodon account.

    Attributes:
        id (uuid): Primary Key for the avatar.
        source_url (str): The URL of the static avatar image on the remote instance.
        cached_avatar (file | None): Our locally cached version of the remote image. Fetched asyncronously.
        cache_stale (bool): Indicates if the cache is stale and needs to be refreshed from remote instance.
        user_account (MastodonUserAuth): OneToOne relationship to MastodonUserAuth.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
    user_account = models.OneToOneField(
        "MastodonUserAuth", on_delete=models.CASCADE, related_name="avatar"
    )

    def __str__(self):  # pragma: nocover
        return f"{self.user_account.account_username} - {self.id} - Stale: {self.cache_stale}"

    class Meta:
        rules_permissions = {
            "add": is_valid_user,
            "read": is_mastodon_avatar_owner,
            "edit": is_mastodon_avatar_owner,
            "delete": is_mastodon_avatar_owner,
            "list": is_valid_user,
        }

    @property
    def img_url(self) -> str | None:
        """
        Returns cached avatar url if exists, source url if not.
        """
        if self.cache_stale or self.cached_avatar is None:
            return self.source_url
        return self.cached_avatar.url  # type: ignore

    def get_avatar(self):
        """
        Calls the async fetch of avatar and saves results to model.
        """
        img_fetch = async_to_sync(self.fetch_avatar)
        img = img_fetch()
        if img is not None:
            self.cached_avatar = img
            self.cache_stale = False
            self.save()

    async def fetch_avatar(self):
        """
        Fetches the current avatar from remote server.
        """
        if self.cache_stale and self.source_url is not None:
            async with httpx.AsyncClient() as client:
                new_img_response = await client.get(self.source_url)
            if new_img_response.status_code == 200:
                new_img = File(
                    BytesIO(new_img_response.content), name=f"{self.id}_cached_avatar"
                )
                return new_img
        return None  # pragma: nocover


class MastodonUserAuth(TimeStampedModel, RemoteUserAuthModel, OwnedModel):
    """
    A user's authentication for given Mastodon account. Only the associated user can see, edit,
    or delete this object.

    Attributes:
        instance_client (MastodonInstanceClient): Foreign key to our defined app for a given instance.
        account_username (str | None): The username for the account. Fetched from instance.
        owner (User): Foreign key to the `AUTH_USER_MODEL`.
        user_oauth_key (str | None): The oauth user key given by the instance.
        user_auth_token (str | None): The auth token used for credentialing on all subsequent user requests.
    """

    instance_client = models.ForeignKey(
        MastodonInstanceClient, on_delete=models.CASCADE
    )
    account_username = models.CharField(max_length=100, null=True, blank=True)
    user_oauth_key = models.CharField(
        max_length=250, null=True, blank=True, help_text=_("Users OAuth code.")
    )
    user_auth_token = models.CharField(
        max_length=250,
        null=True,
        blank=True,
        help_text=_("Current auth token for user session."),
    )
    social_account = models.OneToOneField(
        Account,
        related_name="mastodon_auth",
        on_delete=models.CASCADE,
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

    def get_avatar_url(self) -> str | None:
        """
        Return the avatar_url from the related object.
        """

        return self.avatar.img_url

    def get_username(self) -> str | None:
        """
        Get the username for the account.
        """

        return self.account_username

    def __str__(self):  # pragma: nocover
        return f"{self.user} - @{self.account_username}@{self.instance_client.api_base_url[8:]}"

    class Meta:
        rules_permissions = {
            "add": is_valid_user,
            "read": is_owner,
            "edit": is_owner,
            "delete": is_owner,
            "list": is_valid_user,
        }
