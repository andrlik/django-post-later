from __future__ import annotations

from typing import Tuple

import os
import secrets
from decimal import Decimal

import blurhash
from django.core.files import File
from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel
from PIL import Image

from ..rules import is_owner, is_valid_user
from ..utils import resize_image
from ..validators import validate_focal_field_limit
from .abstract import OwnedModel
from .social_accounts import Account


def media_directory_path(instance, filename):
    """
    Returns upload directory for user media uploads.
    """
    oldfilename, oldextension = os.path.splitext(filename)
    newfilename = secrets.token_urlsafe(20)
    return f"media_uploads/user_{instance.user.id}/%Y/%m/%d/{newfilename}{oldextension}"


def media_thumbnail_directory_path(instance, filename):
    """
    Returns upload directory for thumbnails generated from user media.
    """
    return f"media_uploads/user_{instance.user.id}/thumbnails/%Y/%m/%d/{filename}"


class ScheduledThread(TimeStampedModel, OwnedModel):
    """
    Model representing a scheduled thread that will be delivered
    incrementally to the service target.
    """

    class ThreadStatus(models.TextChoices):
        PENDING = "pending", _("Pending")
        STARTED = "started", _("Started")
        WAITING = "waiting", _("Awaiting Retry")
        COMPLETE = "complete", _("Completed")

    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        help_text=_(
            "Account where this thread is scheduled to be sent.",
        ),
        related_name="schedule_threads",
    )
    seconds_between_posts = models.PositiveIntegerField(
        default=60,
        help_text=_(
            "The number of seconds to wait between posting each subsequent post in the thread."
        ),
    )
    send_at = models.DateTimeField(help_text=_("When to begin publishing the thread."))
    status = models.CharField(
        max_length=10, choices=ThreadStatus.choices, default=ThreadStatus.PENDING
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("If publishing has started, when did it begin?"),
    )
    next_publish = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("If started, when will the next post publish?"),
    )
    finished_at = models.DateTimeField(
        null=True, blank=True, help_text=_("If finished, when was it completed?")
    )
    start_remote_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text=_(
            "If publishing has begun, the first post's remote id on the service."
        ),
    )
    next_id_to_reply = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text=_(
            "If publishing has begun, the next remote id to use for in_reply_to on the service."
        ),
    )
    end_remote_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text=_("If publishing is completed, the final remote id in the thread."),
    )

    @property
    def num_posts(self) -> int:
        """
        Returns the number of posts associated with this thread.
        """
        return self.posts.count()

    class Meta:
        rules_permissions = {
            "add": is_valid_user,
            "read": is_owner,
            "edit": is_owner,
            "delete": is_owner,
            "list": is_valid_user,
        }


class ScheduledPost(TimeStampedModel, OwnedModel):
    """
    Model representing a scheduled post for one or more connected
    services.
    """

    class PostStatus(models.TextChoices):
        PENDING = "pending", _("Pending")
        ERROR = "error", _("Error, awaiting retry.")
        FAILED = "failed", _("Failed to post after multiple retries. Giving up.")
        COMPLETE = "complete", _("Sucessfully posted.")

    thread = models.ForeignKey(
        ScheduledThread,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="posts",
        help_text=_("The scheduled thread this post is a part of."),
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        help_text=_("Account where this post is scheduled to be sent."),
        related_name="schedule_posts",
    )
    thread_ordering = models.IntegerField(
        default=0,
        help_text=_("Used to order posts in a thread. Not used for solo posts."),
    )
    content = models.TextField(help_text=_("What do you want to say?"))
    send_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_(
            "Scheduled time for post. Overriden if part of a scheduled thread."
        ),
    )
    post_status = models.CharField(
        max_length=10,
        choices=PostStatus.choices,
        default=PostStatus.PENDING,
        help_text=_("Status of scheduled post."),
    )
    num_failures = models.PositiveIntegerField(
        default=0, help_text=_("Number of failed attempts to post.")
    )
    next_retry = models.DateTimeField(
        null=True, blank=True, help_text=_("Next time to retry to post.")
    )
    remote_id = models.CharField(
        max_length=100, null=True, blank=True, help_text=_("Remote id of the post.")
    )
    remote_url = models.URLField(
        null=True, blank=True, help_text=_("URL to view post on remote server.")
    )
    finished_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("When post was successfully submitted to remote server."),
    )
    auto_boost_hours = models.IntegerField(
        null=True,
        blank=True,
        help_text=_("If set, how many hours after initial post to boost this again."),
    )

    class Meta:
        rules_permissions = {
            "add": is_valid_user,
            "read": is_owner,
            "edit": is_owner,
            "delete": is_owner,
            "list": is_valid_user,
        }


class MediaAttachment(TimeStampedModel, OwnedModel):
    """
    Model representing a media attachment for a scheduled post.
    """

    media_file = models.FileField(
        upload_to=media_directory_path, help_text=_("Media being uploaded.")
    )
    mime_type = models.CharField(
        "MIME Type",
        help_text=_(
            "Type of media being uploaded. Will attempt to guess from data and file extension."
        ),
        max_length=20,
        blank=True,
    )
    thumbnail = models.ImageField(
        upload_to=media_thumbnail_directory_path,
        null=True,
        blank=True,
        help_text=_("Generated thumbnail of image if available."),
    )
    scheduled_post = models.ForeignKey(
        ScheduledPost,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text=_("The scheduled post this media is attached to."),
        related_name="attachments",
    )
    width = models.PositiveIntegerField(
        null=True, blank=True, help_text=_("Width of media if image.")
    )
    height = models.PositiveIntegerField(
        null=True, blank=True, help_text=_("Height of media if image.")
    )
    video_duration = models.PositiveIntegerField(
        null=True, blank=True, help_text=_("Duration of video, if applicable.")
    )
    alt_text = models.CharField(
        max_length=1000,
        null=True,
        blank=True,
        help_text=_("Description for visually impaired."),
    )
    remote_id = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text=_("Id for media on remote server if sent."),
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

        if self.mime_type.startswith("image/"):
            return True
        return False

    @property
    def is_video(self) -> bool:
        """
        Returns true of the media is a video.
        """
        if self.mime_type.startswith("video/"):
            return True
        return False

    @property
    def is_audio(self) -> bool:
        """
        Returns true if the media type is audio.
        """
        if self.mime_type.startswith("audio/"):
            return True
        return False

    @property
    def is_square_image(self) -> bool:
        """
        Returns true if height and width are set, are both equal and the media is an image.
        """

        if self.is_image and self.height == self.width and self.height is not None:
            return True
        return False

    def generate_thumbnail(self) -> None:
        """
        Generate a thumbnail version of the image, and save the result to the model.
        Only works if the source media is an image.
        """

        if not self.is_image:
            raise ValueError("Cannot generate a thumbnail from a video.")
        thumb = resize_image(self.media_file, 200, 200)
        with Image.open(thumb, "rb") as thumb_img:
            hash = blurhash.encode(thumb_img.to_bytes(), x_components=3, y_components=3)
        self.thumbnail = File(thumb_img.to_bytes(), name=f"thumb_{hash}")
        self.save()

    class Meta:
        rules_permissions = {
            "add": is_valid_user,
            "read": is_owner,
            "edit": is_owner,
            "delete": is_owner,
            "list": is_valid_user,
        }
