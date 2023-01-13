from __future__ import annotations

from typing import Iterable, Tuple, Any

import os
import secrets
from datetime import timedelta
from decimal import Decimal

import blurhash
from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.files import File
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel
from PIL import Image
from rules.contrib.models import RulesModel

from ..exceptions import EmptyThreadException, ThreadAlreadyComplete
from ..rules import is_social_content_owner, is_valid_user
from ..utils import resize_image
from ..validators import validate_focal_field_limit
from .abstract import UUIDModel
from .social_accounts import Account


def media_directory_path(instance, filename):
    """
    Returns upload directory for user media uploads.
    """
    oldfilename, oldextension = os.path.splitext(filename)
    newfilename = secrets.token_urlsafe(20)
    return f"media_uploads/user_{instance.account.user.id}/%Y/%m/%d/{newfilename}{oldextension}"


def media_thumbnail_directory_path(instance, filename):
    """
    Returns upload directory for thumbnails generated from user media.
    """
    return (
        f"media_uploads/user_{instance.account.user.id}/thumbnails/%Y/%m/%d/{filename}"
    )


class PostStatus(models.TextChoices):
    """
    Default choices for ScheduledSendModel.
    """

    PENDING = "pending", _("Pending")
    ERROR = "error", _("Error, awaiting retry.")
    FAILED = "failed", _("Failed to post after multiple retries. Giving up.")
    QUEUED = "queued", _("Queued on remote server")
    COMPLETE = "complete", _("Sucessfully posted.")


class BaseScheduledSendModel(TimeStampedModel, UUIDModel, RulesModel):
    """
    Abstract model that represents an item that needs to be sent a remote account with
    the ability to try, log failures, and retry later to a remote service.

    NOTE: You will need to specify the `account` ForeignKey when you subclass this in
    order to have comprehensible related names.

    Attributes:
        status_choices (models.TextChoices): choice object for the status info.
        account (models.ForeignKey): Define this for each so that can set the related_name.
        status (str): Current status of object.
        send_at (datetime): When this item is scheduled to send.
        num_failures (int): Number of failed attempts to send.
        next_retry (datetime | None): When the next retry is scheduled for.
        remote_id (str | None): Remote id of the published item on the target server.
        remote_url (str | None): Remote URL of the published item on the target server.
        queued_at (datetime | None): If target server supports queueing, what time was it successfully added to the queue.
        remote_queue_id (str | None): If the target server supports queueing, what id did it assign to the object.
        finished_at (datetime | None): When was the item fully published.
    """

    status_choices: models.TextChoices = PostStatus
    account: models.ForeignKey

    send_at = models.DateTimeField(
        help_text=_("When to initiate sending to remote system."), db_index=True
    )
    status = models.CharField(
        max_length=20,
        choices=status_choices.choices,
        default=status_choices.PENDING,
        help_text=_("Current status of object."),
        db_index=True,
    )
    num_failures = models.PositiveIntegerField(
        default=0, help_text=_("Number of failed attempts to send.")
    )
    last_attempt_at = models.DateTimeField(
        null=True, blank=True, help_text=_("When was the last failed attempt occur?")
    )
    next_retry = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("If failed, when is the next attempt to send."),
        db_index=True,
    )
    remote_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text=_("Id of sent item on the remote system."),
    )
    remote_url = models.URLField(
        null=True, blank=True, help_text=_("URL of sent item on the remote system.")
    )
    queued_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_(
            "If the remotes system supports queuing, what time did we successfully queue for?"
        ),
    )
    remote_queue_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text=_("What remote id did the target server give to the queued object?"),
    )
    finished_at = models.DateTimeField(
        null=True, blank=True, help_text=_("When item was successfully sent.")
    )

    def send_item(self) -> bool:
        """
        Attempt to send the item via the `account` object and return a bool
        indicating success or failure.
        """
        pass

    async def asend_item(self) -> bool:
        """
        Attempt to send the item using a coroutine.
        """
        pass

    def schedule_retry(self) -> None:
        """
        Set status to ERROR, schedule next retry, or declare the post a failure.
        """
        if self.num_failures == settings.MAX_POST_FAILURES - 1:
            self.status = type(self).status_choices.FAILED
        else:
            self.status = type(self).status_choices.ERROR
        self.num_failures = models.F("num_failures") + 1
        self.next_retry = timezone.now() + timedelta(
            seconds=settings.POST_FAILURE_RETRY_WAIT
        )
        self.save()

    aschedule_retry = sync_to_async(schedule_retry)

    @classmethod
    async def find_jobs(cls) -> dict[str, Iterable]:
        """
        Find posts scheduled to send, retry, or follow-up on.

        Returns a dict with four keys, each containing a Queryset: `to_send`, `retry`,`followup`.
        """
        raise NotImplementedError

    class Meta:
        abstract = True


class ScheduledThread(BaseScheduledSendModel):
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
        ERROR = "error", _("Error, Awaiting Retry")
        COMPLETE = "complete", _("Completed")

    status_choices = ThreadStatus

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
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("If publishing has started, when did it begin?"),
    )
    next_publish = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("If started, when will the next post publish?"),
        db_index=True,
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

    async def get_posts(self, pending_only: bool = False) -> Iterable:
        """
        Fetch the posts in the thread in order. Optionally limit it to posts
        that are awaiting sending.

        Args:
            pending_only (bool): Only grab posts that are pending or awaiting retry.

        Returns a Queryset.
        """
        posts = self.posts.all()
        if pending_only:
            posts = posts.filter(
                post_status__in=[
                    ScheduledPost.PostStatus.PENDING,
                    ScheduledPost.PostStatus.ERROR,
                ]
            )
        return posts.order_by("thread_ordering")

    async def get_next_post(self) -> ScheduledPost:
        """
        Fetch the next post that needs to be sent.
        """
        return await self.get_posts(pending_only=True).afirst()

    async def send_next_post(self) -> bool:
        """
        Looks up the next pending/retry post in the thread and attempts to send it.

        Returns a bool indicating if the send was successful or not.
        """
        if self.status in [self.ThreadStatus.FAILED, self.ThreadStatus.COMPLETE]:
            raise ThreadAlreadyComplete
        try:
            next_post = await self.get_next_post()
        except ObjectDoesNotExist:
            raise EmptyThreadException
        result = await next_post.send_post()
        next_post = await ScheduledPost.objects.aget(id=next_post.id)
        if result:
            if self.start_remote_id is None:
                self.start_remote_id = next_post.remote_id
            self.next_id_to_reply = next_post.remote_id
            self.next_publish = timezone.now() + timedelta(
                seconds=self.seconds_between_posts
            )
            posts_left = await self.get_posts(pending_only=True).count()
            if posts_left > 0:
                self.status = self.ThreadStatus.STARTED
            else:
                self.status = self.ThreadStatus.COMPLETE
                self.end_remote_id = next_post.remote_id
                self.finished_at = timezone.now()
            sync_to_async(self.save())
            return True
        else:
            sync_to_async(self.schedule_retry(next_post))
        return False

    def schedule_post_retry(self, post: ScheduledPost) -> None:
        """
        Scheduled the next retry for the post and evaluates if the thread should give up.
        """
        self.last_attempt_at = timezone.now()
        self.num_failures = models.F("num_failures") + 1
        if post.status == PostStatus.FAILED:
            self.status = self.status_choices.FAILED
        else:
            self.status = self.status_choices.ERROR
            self.next_retry = timezone.now() + timedelta(
                seconds=settings.POST_FAILURE_RETRY_WAIT
            )
        self.save()

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
            ),
            "next_post": cls.objects.filter(
                status=cls.ThreadStatus.STARTED, next_publish__lte=current_time
            ),
            "retries": cls.objects.filter(
                status=cls.ThreadStatus.ERROR, next_retry__lte=current_time
            ),
        }

    class Meta:
        rules_permissions = {
            "add": is_valid_user,
            "read": is_social_content_owner,
            "edit": is_social_content_owner,
            "delete": is_social_content_owner,
            "list": is_valid_user,
        }


class ScheduledPost(BaseScheduledSendModel):
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
        status (str): Status of this post. One of "pending", "error", "failed", "queued", or "complete.
        num_failures (int): Number of failures encountered sending this post.
        next_retry (datetime | None): If failure has occurred, next scheduled attempt to send.
        remote_id (str | None): Remote id of the post once sent.
        remote_url (str | None): URL of the post on the remote server.
        finished_at (datetime | None): When the post was successfully sent.
        auto_boost_hours (int | None): How many hours after initial post to boost it again.
    """

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

    @classmethod
    async def find_jobs(cls) -> dict[str, Iterable]:
        """
        Find posts scheduled to send, retry, or follow-up on.

        Returns a dict with four keys, each containing a Queryset: `to_send`, `retry`,`followup`.
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
        }

    class Meta:
        rules_permissions = {
            "add": is_valid_user,
            "read": is_social_content_owner,
            "edit": is_social_content_owner,
            "delete": is_social_content_owner,
            "list": is_valid_user,
        }


class ScheduledBoost(BaseScheduledSendModel):
    """
    Model representing a scheduled boost/retweet for a given remote post.

    Attributes:
        account (Account): Foreign Key to social account.
        boost_status (str): The current status of the boost.
        remote_url (str): URL of the remote post to boost.
        remote_id (str | None): Derived remote id of the post, if any.
        send_at (datetime): When should this boost be sent.
        last_attempt_at (datetime | None): Last failed attempt to send.
        num_failures (int): Number of failures so far.
        next_retry (datetime | None): Next scheduled retry to send.
        finished_at (datetime | None): When was boost successfully sent?
    """

    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        help_text=_("Social account this is linked to."),
        related_name="scheduled_boosts",
    )

    async def send_boost(self) -> bool:
        """
        Attempts to send the boost to the remote service.

        Returns bool to indicate if it was successful or not.
        """
        pass

    @classmethod
    async def find_jobs(cls) -> dict[str, Iterable]:
        """
        Finding pending tasks to boost or retry. Returns a
        dict of Querysets with two keys: "boosts", "retries".
        """
        current_time = timezone.now()
        return {
            "boosts": cls.objects.filter(
                boost_status=cls.BoostStatus.PENDING, send_at__lte=current_time
            ),
            "retries": cls.objects.filter(
                boost_status=cls.BoostStatus.ERROR, next_retry__lte=current_time
            ),
        }

    class Meta:
        rules_permissions = {
            "add": is_valid_user,
            "read": is_social_content_owner,
            "edit": is_social_content_owner,
            "delete": is_social_content_owner,
            "list": is_valid_user,
        }


class MediaAttachment(TimeStampedModel, UUIDModel, RulesModel):
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

    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        help_text=_("Social account this media is associated with."),
    )
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

        return (self.focus_x, self.focus_y)  # pragma: nocover

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
            min_age (int): Minimum age in days.

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
            "read": is_social_content_owner,
            "edit": is_social_content_owner,
            "delete": is_social_content_owner,
            "list": is_valid_user,
        }
