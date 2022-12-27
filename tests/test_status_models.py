import pytest
from django.core.files import File

from post_later.models.statuses import (
    MediaAttachment,
    media_directory_path,
    media_thumbnail_directory_path,
)

pytestmark = pytest.mark.django_db(transaction=True)


def test_media_path(mastodon_keyed_auth, img_bytes):
    source_image = File(img_bytes, name="IMG_0008.jpeg")
    media = MediaAttachment.objects.create(
        media_file=source_image, mime_type="image/jpeg", user=mastodon_keyed_auth.user
    )
    validation_str = media_directory_path(media, filename="IMG_0008.jpeg")
    assert "IMG_0008.jpeg" not in validation_str
    assert validation_str.endswith(".jpeg")
    assert f"user_{mastodon_keyed_auth.user.id}" in validation_str


def test_thumb_media_path(mastodon_keyed_auth, img_bytes):
    source_image = File(img_bytes, name="thumb_IMG_0008.jpeg")
    media = MediaAttachment.objects.create(
        media_file=source_image, mime_type="image/jpeg", user=mastodon_keyed_auth.user
    )
    validation_str = media_thumbnail_directory_path(
        media, filename="thumb_IMG_0008.jpeg"
    )
    assert validation_str.endswith("thumb_IMG_0008.jpeg")
    assert "/thumbnails/" in validation_str
    assert f"user_{mastodon_keyed_auth.user.id}" in validation_str
