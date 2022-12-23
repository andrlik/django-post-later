from __future__ import annotations

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
    """

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
    """

    def get_avatar(self) -> str | None:
        """
        Fetch the avatar url we are using if it exists.
        """
        raise NotImplementedError(self.__class__.__name__ + "get_avatar")

    def get_username(self) -> str | None:
        """
        Get the username of the account if already retrieved.
        """
        raise NotImplementedError(self.__class__.__name__ + "get_username")

    def upload_media(self, media_object: File) -> str | None:
        """
        Upload a given media file to the remote server and return the media id.
        """
        raise NotImplementedError(self.__class__.__name__ + "upload_media")

    def send_post(
        self,
        content: str,
        media_ids: list[str] = [],
        schedule_time: datetime | None = None,
    ) -> str | None:
        """
        Sends the post to the remote server and either returns the remote id as a string
        or raises an exception on error.
        """
        raise NotImplementedError(self.__class__.__name__ + "send_post")

    def get_remote_url(self) -> str | None:
        """
        Return the url of the post on the remote server.
        """
        raise NotImplementedError(self.__class__.__name__ + "get_remote_url")

    class Meta:
        abstract = True
