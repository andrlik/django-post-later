from __future__ import annotations

import uuid
from datetime import datetime

from django.conf import settings
from django.core.files import File
from django.db import models
from django.utils.translation import gettext_lazy as _
from rules.contrib.models import RulesModel

from ..rules import is_owner, is_valid_user


class OwnedModel(RulesModel):
    """
    An abstract model class that implements the basic ownership model
    and rules meta permission pattern.

    Attributes:
        id (uuid): Primary key for the model.
        user (AUTH_USER_MODEL): Foreign key to the associated instance of the project's `AUTH_USER_MODEL`.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text=_("The user object that owns this instance."),
    )

    class Meta:
        abstract = True
        rules_permissions = {
            "add": is_valid_user,
            "read": is_owner,
            "edit": is_owner,
            "delete": is_owner,
            "list": is_valid_user,
        }


class RemoteUserAuthModel(models.Model):
    """
    Abstract model that enables a consistent API for remote accounts.
    Any connecting auth model intended to be used with `post_later.models.social_accounts.Account`
    must be a subclass of this model.

    Attributes:
        allows_remote_queueing (bool): Does this service support sending posts to be scheduled on the remote server?
    """

    allows_remote_queuing: bool

    def get_avatar_url(self) -> str | None:
        """
        Fetch the avatar url we are using if it exists.
        """
        raise NotImplementedError(
            self.__class__.__name__ + "get_avatar_url"
        )  # pragma: nocover

    def get_username(self) -> str | None:
        """
        Get the username of the account if already retrieved.
        """
        raise NotImplementedError(
            self.__class__.__name__ + "get_username"
        )  # pragma: nocover

    def get_remote_url(self) -> str | None:
        """
        Get the profile URL on the social service.
        """
        raise NotImplementedError(
            self.__class__.__name__ + "get_remote_url"
        )  # pragma: nocover

    def upload_media(self, media_object: File) -> str | None:
        """
        Upload a given media file to the remote server and return the media id.
        """
        raise NotImplementedError(
            self.__class__.__name__ + "upload_media"
        )  # pragma: nocover

    def send_post(
        self,
        content: str,
        media_ids: list[str] = [],
        in_response_to_id: str | None = None,
        schedule_time: datetime | None = None,
    ) -> tuple[str, str | None]:
        """
        Sends the post to the remote server and either returns the remote id as a string
        or raises an exception on error.

        Returns a tuple of the remote id and remote url of the post. The url will be None if a scheduled post.
        """
        raise NotImplementedError(
            self.__class__.__name__ + "send_post"
        )  # pragma: nocover

    def username_search(self, name_fragment: str) -> list[str]:
        """
        Given a fragment of a username, attempt to do a search on the remote server for use in
        tagging other accounts in a scheduled post.
        """
        raise NotImplementedError(
            self.__class__.__name__ + "username_search"
        )  # pragma: nocover

    @property
    def is_ready_post(self) -> bool:
        """
        Validates if the user auth object is fully authenticated
        and ready to post.
        """

        raise NotImplementedError(
            self.__class__.__name__ + "is_ready_post"
        )  # pragma: nocover

    class Meta:
        abstract = True
