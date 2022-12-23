from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel

from ..rules import is_owner, is_valid_user
from .abstract import OwnedModel


class Account(TimeStampedModel, OwnedModel):
    """
    Represents a remote social account that's a valid target to use in posting.

    Attributes:
        account_type (str): The type of social account this represents, e.g. Mastodon
        account_status (str): The status of this account if not active.
        username (str): The username associated with this account.
    """

    class AccountType(models.TextChoices):
        MASTODON = "mast", _("Mastodon")
        TWITTER = (
            "twitter",
            _("Twitter"),
        )
        INSTAGRAM = "insta", _("Instagram")

    class AccountStatus(models.TextChoices):
        PENDING = "pending", _("Created, but not authenticated yet.")
        ACTIVE = "active", _("Active account")
        TRASHED = "trash", _("Pending deletion...")

    account_type = models.CharField(
        max_length=10,
        choices=AccountType.choices,
        default=AccountType.MASTODON,
        help_text=_("What type of social account is this?"),
    )
    account_status = models.CharField(
        max_length=10,
        choices=AccountStatus.choices,
        default=AccountStatus.PENDING,
        help_text=_("Status of account."),
    )
    username = models.CharField(
        max_length=250, null=True, blank=True, help_text=_("Username of account")
    )

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
    """

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
