from __future__ import annotations

from typing import Iterable, Tuple

import os
import secrets
from datetime import timedelta
from decimal import Decimal

import blurhash
from django.conf import settings
from django.core.files import File
from django.db import models
from django.utils import timezone
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

    Attributes:
        account (Account): The social account this thread is to be sent.
        seconds_between_posts (int): The number of seconds to wait between posts within the thread. Default 60.
        send_at (datetime): When to begin posting the thread.
        status (str): Current status of the thread. One of "pending", "started", "waiting", "complete".
        started_at (datetime | None): When did this thread first begin sending posts.
        next_publish (datetime | None): When the next post will be sent.
        finished_at (datetime | None): When the thread finished sending all posts.
        start_remote_id (str | None): Remote id of the first post in the thread.
        next_id_to_reply (str | None): Remote post id to reply to for next post in thread.
        end_remote_id (str | None): Remote id of the last post in the thread.
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
    next_retry = models.DateTimeField(
        null=True, blank=True, help_text=_("If in error, when will we retry next?")
    )
    num_failures = models.PositiveIntegerField(
        default=0,
        help_text=_("Number of failures encountered so far sending this thread."),
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

    @classmethod
    async def find_jobs(cls) -> dict[str, Iterable]:
        """
        Find threads that need to have posts sent.
        If their scheduled send is in the past, their next_retry is now past, or next_publish has past.

        Returns a dict with three keys and a Queryset for each: "to_start", "next_post", "retries".
        """
        current_time = timezone.now()
        return {
            "to_start": cls.objects.filter(
                status=cls.ThreadStatus.PENDING, send_at__lte=current_time
            ).exclude(finished_at__notnull=True),
            "next_post": cls.objects.filter(
                status=cls.ThreadStatus.STARTED, next_publish__lte=current_time
            ).exclude(finished_at__notnull=True),
            "retries": cls.objects.filter(
                status=cls.ThreadStatus.WAITING, next_retry__lte=current_time
            ).exclude(finished_at__notnull=True),
        }

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

    Attributes:
        thread (ScheduledThread | None): If part of thread, this will be that link.
        account (Account): The account this post is going to be sent to.
        thread_ordering (int): The order number of this post in the thread, if applicable.
        content (str): The text content of the post.
        send_at (datetime | None): The time this post is scheduled to send. If part of a thread, the thread's send time is used.  # noqa: E501
        queued_at (datetime | None): If queued on the remote server, i.e. Mastodon, when did we successfully send this?
        remote_queue_id (str | None): If queued on the remote server, i.e. Mastodon, what's the scheduled status id?
        post_status (str): Status of this post. One of "pending", "error", "failed", "queued", or "complete.
        num_failures (int): Number of failures encountered sending this post.
        next_retry (datetime | None): If failure has occurred, next scheduled attempt to send.
        remote_id (str | None): Remote id of the post once sent.
        remote_url (str | None): URL of the post on the remote server.
        finished_at (datetime | None): When the post was successfully sent.
        auto_boost_hours (int | None): How many hours after initial post to boost it again.
    """

    class PostStatus(models.TextChoices):
        PENDING = "pending", _("Pending")
        ERROR = "error", _("Error, awaiting retry.")
        FAILED = "failed", _("Failed to post after multiple retries. Giving up.")
        QUEUED = "queued", _("Queued on remote server")
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
    queued_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Time this was successfully queued on the remote server."),
    )
    remote_queue_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text=_("Schedule post id if queued on remote server."),
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

    async def send_post(self) -> bool:
        """
        Attempt to send this post via the account. If fails, automatically queues a retry.
        If failures exceed threshold, changes status to FAILED and gives up.

        Returns a bool indicating whether it was successful.
        """
        # remote_media_ids = []
        async for attachment in self.attachments.all():
            pass
        return False

    def schedule_retry(self) -> None:
        """
        Set status to ERROR, schedule next retry, or declare the post a failure.
        """
        if self.num_failures == settings.MAX_POST_FAILURES - 1:
            self.post_status = type(self).PostStatus.FAILED
        else:
            self.post_status = type(self).PostStatus.ERROR
        self.num_failures = models.F("num_failures") + 1
        if self.thread is None:
            self.next_retry = timezone.now() + timedelta(
                seconds=settings.POST_FAILURE_RETRY_WAIT
            )
        self.save()

    @classmethod
    async def find_jobs(cls) -> dict[str, Iterable]:
        """
        Find posts scheduled to send, retry, or follow-up on.

        Returns a dict with four keys, each containing a Queryset: `to_send`, `retry`,`followup`, `boosts`.
        """
        current_time = timezone.now()
        return {
            "to_send": cls.objects.filter(
                post_status=cls.PostStatus.PENDING, send_at__lte=current_time
            ).exclude(thread__notnull=True),
            "retry": cls.objects.filter(
                post_status=cls.PostStatus.ERROR, next_retry__lte=current_time
            ).exclude(thread__notnull=True),
            "followup": cls.objects.filter(
                post_status=cls.PostStatus.QUEUED, send_at__lte=current_time
            ).exclude(thread__notnull=True),
            "boosts": cls.objects.filter(
                post_status=cls.PostStatus.COMPLETE,
                auto_boost_hours__notnull=True,
                auto_boost_completed=False,
            ),
        }

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
    Model representing a media attachment for a scheduled post. Initially uploaded before the post
    is created, so we'll need a class method to clean up orphans that we can run periodically.

    Attributes:
        media_file (File): The file being uploaded. Must be an image or video.
        mime_type (str): The introspected mime_type of the file.
        thumbnail (ImageFile): A thumbnail, if available, for the file.
        scheduled_post (ScheduledPost | None): The ScheduledPost to which this is attached.
        width (int | None): For images, what is the width of the image.
        height (int | None): For images, what is the height of the image.
        video_duration (int | None): If a video, what is the duration in seconds?
        alt_text (str | None): Description of the media for the visually impaired.
        remote_id (str | None): Remote id of the post after successfully posted.
        focus_x (Decimal): Value between -1.0 to 1.0 for focus on the x-axis.
        focus_y (Decimal): Value between -1.0 to 1.0 for focus on the y-axis.
    """

    class UploadStatus(models.TextChoices):
        PENDING = "pending", _("Pending")
        ERROR = "error", _("Error, awaiting retry")
        FAILED = "failed", _("Failed to upload after multiple attempts.")
        COMPLETE = "complete", _("Uploaded successfully")

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
    upload_status = models.CharField(
        max_length=15,
        choices=UploadStatus.choices,
        default=UploadStatus.PENDING,
        help_text=_("Status of the remote upload to service."),
    )
    num_failures = models.PositiveIntegerField(
        default=0, help_text=_("Number of failures to upload this piece of media.")
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
    duration = models.PositiveIntegerField(
        null=True, blank=True, help_text=_("Duration of video or audio, if applicable.")
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

    async def upload_media(self) -> str:
        """
        Attempt to upload the media to the remote server and return the remote id.
        """
        pass

    @classmethod
    async def clean_orphans(cls, min_age: int) -> int:
        """
        Clear out orphaned media files more than `min_age` days old.
        Args:
            min_age (int): Minumum age in days.

        Returns number of records deleted.
        """
        cutoff_date = timezone.now() - timedelta(days=min_age)
        num_deleted, objects_removed = await cls.objects.filter(
            scheduled_post__isnull=True, created__lt=cutoff_date
        ).adelete()
        return num_deleted

    class Meta:
        rules_permissions = {
            "add": is_valid_user,
            "read": is_owner,
            "edit": is_owner,
            "delete": is_owner,
            "list": is_valid_user,
        }
