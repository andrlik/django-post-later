from __future__ import annotations

from typing import Tuple

from decimal import Decimal

import blurhash
from django.core.files import File
from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel
from PIL import Image

from ..rules import is_owner, is_valid_user
from ..validators import validate_focal_field_limit
from .abstract import OwnedModel


class AbstractMediaUpload(OwnedModel):

    mime_type = models.CharField(
        "MIME Type",
        help_text=_(
            "Type of media being uploaded. Will attempt to guess from file extension."
        ),
        max_length=20,
    )
    media_group = models.ForeignKey(
        "MediaGroup",
        on_delete=models.CASCADE,
        help_text=_("Group of media that will be attached to a post."),
    )
    alt_text = models.CharField(
        max_length=1000,
        null=True,
        blank=True,
        help_text=_("Description for visually impaired."),
    )
    focus_x = models.DecimalField(
        default=0.00,
        max_digits=3,
        decimal_places=2,
        validators=[validate_focal_field_limit],
    )
    focus_y = models.DecimalField(
        default=0.00,
        max_digits=3,
        decimal_places=2,
        validators=[validate_focal_field_limit],
    )

    @property
    def focus(self) -> Tuple[Decimal, Decimal]:
        """
        Return the focus property as a tuple.
        """

        return (self.focus_x, self.focus_y)

    @property
    def is_image(self) -> bool:
        """
        Returns a bool if the mime_type of the file is an image.
        """

        if self.mime_type in [
            "image/bmp",
            "image/gif",
            "image/jpeg",
            "image/png",
            "image/tiff",
            "image/webp",
        ]:
            return True
        return False

    class Meta:
        abstract = True


class MediaGroup(TimeStampedModel, OwnedModel):
    """
    A model representing a collection of media to be included in
    a given social media post.
    """

    class Meta:
        rules_permissions = {
            "add": is_valid_user,
            "read": is_owner,
            "edit": is_owner,
            "delete": is_owner,
            "list": is_valid_user,
        }


def media_directory_path(instance, filename):
    """
    Returns upload directory for user media uploads.
    """

    return f"media_uploads/user_{instance.user.id}/%Y/%m/%d/"


def media_thumbnail_directory_path(instance, filename):
    """
    Returns upload directory for thumbnails generated from user media.
    """

    return f"media_uploads/user_{instance.user.id}/thumbnails/%Y/%m/%d/"


class ImageMedia(TimeStampedModel, AbstractMediaUpload):
    """
    A model representing an individual media upload for a given post.

    Attributes:
        img The original file uploaded to the server. Note that some post processing may be required.
        thumbnail: Storage object representing a generated thumbnail for images.
    """

    img = models.ImageField(
        upload_to=media_directory_path, help_text=_("Image file being uploaded.")
    )
    thumbnail = models.ImageField(
        upload_to=media_thumbnail_directory_path,
        null=True,
        blank=True,
        help_text=_("Generated thumbnail for images."),
    )

    @property
    def is_square_image(self) -> bool:
        """
        If an image file, check that it's also square for Instagram.
        """
        return self.img.width == self.img.height

    def generate_thumbnail(self) -> None:
        """
        Generate a thumbnail version of the image.
        """

        with Image.open(self.img.open("rb")) as img:
            orig_width, orig_height = img.size
            if orig_width > 200 or orig_width > 200:
                thumb = img.copy().thumbnail(size=(200, 200))
            else:
                thumb = img.copy()
        hash = blurhash.encode(thumb.to_bytes(), x_components=3, y_components=3)
        self.thumbnail = File(thumb.to_bytes(), name=f"thumb_{hash}")
        self.save()

    class Meta:
        rules_permissions = {
            "add": is_valid_user,
            "read": is_owner,
            "edit": is_owner,
            "delete": is_owner,
            "list": is_valid_user,
        }


class VideoMedia(TimeStampedModel, AbstractMediaUpload):
    """
    A model representing a video item of media that is uploaded.

    video: The original file that was uploaded.
    """

    video = models.FileField(
        upload_to=media_directory_path, help_text=_("Media being uploaded.")
    )
    duration = models.IntegerField(
        null=True, blank=True, help_text=_("Calculated duration of video.")
    )

    class Meta:
        rules_permissions = {
            "add": is_valid_user,
            "read": is_owner,
            "edit": is_owner,
            "delete": is_owner,
            "list": is_valid_user,
        }
