from __future__ import annotations

from typing import Optional

import uuid

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel

from ..rules import is_owner, is_valid_user
from .abstract import OwnedModel, RemoteUserAuthModel


class Account(TimeStampedModel, OwnedModel):
    """
    Represents a remote social account that's a valid target to use in posting.

    Attributes:
        account_type (str): The type of social account this represents, e.g. Mastodon
        account_status (str): The status of this account if not active.
        username (str): The username associated with this account.
        auth_content_type (ContentType): foreign key to the content type of the related auth object.
        auth_object_id (uuid): Primary key of the related auth object.
        auth_object: Foreign Key to the related auth object.
    """

    class AccountType(models.TextChoices):
        MASTODON = "mastodon", _("Mastodon")
        TWITTER = (
            "twitter",
            _("Twitter"),
        )
        INSTAGRAM = "instagram", _("Instagram")

    class AccountStatus(models.TextChoices):
        PENDING = "pending", _("Created, but not authenticated yet.")
        ACTIVE = "active", _("Active account")
        TRASHED = "trash", _("Pending deletion...")

    account_type = models.CharField(
        max_length=20,
        choices=AccountType.choices,
        default=AccountType.MASTODON,
        help_text=_("What type of social account is this?"),
        db_index=True,
    )
    account_status = models.CharField(
        max_length=10,
        choices=AccountStatus.choices,
        default=AccountStatus.PENDING,
        help_text=_("Status of account."),
        db_index=True,
    )

    @cached_property
    def auth_object(self) -> Optional[RemoteUserAuthModel]:
        """
        Return the related auth model instance for the given account.
        """
        try:
            oauth_object = getattr(self, f"{self.account_type}_auth")
            if isinstance(oauth_object, RemoteUserAuthModel):
                return oauth_object
            else:
                raise ValueError(  # pragma: nocover
                    "Auth object is not a subclass of RemoteUserAuthModel!"
                )
        except ObjectDoesNotExist:
            return None

    @cached_property
    def username(self) -> str | None:
        """
        Query the username from the auth object if it exists.
        """

        if self.auth_object is not None:
            return self.auth_object.get_username()
        return None

    @cached_property
    def avatar_url(self) -> str | None:
        """
        Get the avatar url from the auth object if it exists.
        """

        if self.auth_object is not None:
            return self.auth_object.get_avatar_url()
        return None

    @cached_property
    def remote_url(self) -> str | None:
        """
        Get the remote URL for the account profile.
        """

        if self.auth_object is not None:
            return self.auth_object.get_remote_url()
        return None  # pragma: nocover

    def refresh_from_db(self, *args, **kwargs):  # pragma: nocover
        """
        Refresh this account from the db, and clear any cached_properties.
        """

        super().refresh_from_db(*args, **kwargs)
        cached_properties = ["auth_object", "username", "avatar_url"]
        for property in cached_properties:
            try:
                del self.__dict__[property]
            except KeyError:  # pragma: nocover
                pass

    def __str__(self):  # pragma: nocover
        return f"{self.username} ({self.get_account_type_display()}) [{self.get_account_status_display()}]"

    class Meta:
        rules_permissions = {
            "add": is_valid_user,
            "read": is_owner,
            "edit": is_owner,
            "delete": is_owner,
            "list": is_valid_user,
        }


class AccountStats(TimeStampedModel, models.Model):
    """
    Represents stats per account based on our usage.

    Attributes:
        id (uuid): Primary key of the stats object.
        account (Account): Foreign key to the related account object.
        num_posts_scheduled (int): Total number of posts that have been scheduled for this account.
        num_posts_sent (int): Total number of posts successfully sent for this account.
        num_threads_scheduled (int): Total number of threads that have been scheduled for this account.
        num_threads_sent (int): Total number of threads successfully sent for this account.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.OneToOneField(
        Account, on_delete=models.CASCADE, related_name="stats"
    )
    num_posts_scheduled = models.PositiveIntegerField(
        default=0,
        help_text=_("Number of posts scheduled for this account over all time."),
    )
    num_posts_sent = models.PositiveIntegerField(
        default=0,
        help_text=_("Total number of posts successfully sent for this account."),
    )
    num_threads_scheduled = models.PositiveIntegerField(
        default=0, help_text=_("Total number of threads scheduled for this account.")
    )
    num_threads_sent = models.PositiveIntegerField(
        default=0, help_text=_("Total number of threads sent for this account.")
    )

    def __str__(self):  # pragma: no cover
        return f"{self.account.username} stats"
