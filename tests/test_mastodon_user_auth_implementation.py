"""
Test that the mastodon user auth model properly implements all the API methods
that social account objects will expect to be able to use.
"""
from __future__ import annotations

from typing import Any

from datetime import datetime, timedelta
from io import BytesIO

import pytest
import responses
from django.contrib.auth.models import AbstractBaseUser
from django.core.files import File
from django.utils import timezone

from post_later.models.mastodon import MastodonAvatar, MastodonUserAuth
from post_later.models.social_accounts import Account

pytestmark = pytest.mark.django_db(transaction=True)


User = AbstractBaseUser


def test_get_missing_auth_object(user: User) -> None:
    account = Account.objects.create(user=user)  # type: ignore
    assert account.auth_object is None
    assert account.username is None
    assert account.avatar_url is None


def test_get_uncached_avatar_url(mastodon_uncached_avatar: MastodonAvatar) -> None:
    assert (
        mastodon_uncached_avatar.user_account.social_account.avatar_url
        == mastodon_uncached_avatar.img_url
    )


def test_get_cached_avatar_url(mastodon_cached_avatar: MastodonAvatar) -> None:
    assert (
        mastodon_cached_avatar.user_account.social_account.avatar_url
        == mastodon_cached_avatar.img_url
    )


def test_get_blank_username(mastodon_pending_user_auth: MastodonUserAuth) -> None:
    assert mastodon_pending_user_auth.social_account.username is None


def test_get_completed_username(mastodon_keyed_auth: MastodonUserAuth) -> None:
    assert (
        mastodon_keyed_auth.social_account.username
        == mastodon_keyed_auth.account_username
    )


def test_get_blank_remote_url(mastodon_pending_user_auth: MastodonUserAuth) -> None:
    assert mastodon_pending_user_auth.social_account.remote_url is None


def test_get_completed_url(mastodon_active_auth: MastodonUserAuth) -> None:
    assert (
        mastodon_active_auth.social_account.remote_url
        == f"{mastodon_active_auth.instance_client.api_base_url}/@johnnyFive"
    )


@pytest.mark.xfail
def test_upload_media(
    mastodon_keyed_auth: MastodonUserAuth, img_bytes: BytesIO
) -> None:
    img_file = File(img_bytes, name="test_image.jpeg")
    media_rsp = responses.Response(
        method="POST",
        url=f"{mastodon_keyed_auth.instance.api_base_url}/api/v2/media",
        status=200,
        json={
            "id": "22348641",
            "type": "image",
            "url": "https://files.mastodon.social/media_attachments/files/022/348/641/original/e96382f26c72a29c.jpeg",
            "preview_url": "https://files.mastodon.social/media_attachments/files/022/348/641/small/e96382f26c72a29c.jpeg",  # noqa: E501
            "remote_url": None,
            "text_url": "https://mastodon.social/media/4Zj6ewxzzzDi0g8JnZQ",
            "meta": {
                "focus": {"x": -0.42, "y": 0.69},
                "original": {
                    "width": 640,
                    "height": 480,
                    "size": "640x480",
                    "aspect": 1.3333333333333333,
                },
                "small": {
                    "width": 461,
                    "height": 346,
                    "size": "461x346",
                    "aspect": 1.3323699421965318,
                },
            },
            "description": "test uploaded via api",
            "blurhash": "UFBWY:8_0Jxv4mx]t8t64.%M-:IUWGWAt6M}",
        },
    )
    responses.add(media_rsp)
    assert mastodon_keyed_auth.upload_media(img_file) == "22348641"


@pytest.mark.xfail
@pytest.mark.parametrize(
    "content,media_ids,in_reply_to_id,schedule_time",
    [
        ("I would like to have some ice cream.", [], None, None),
        ("I would like to have THIS ice cream.", ["8272389"], None, None),
        ("Your ice cream looks good and I want it.", ["837837762"], "83761261", None),
        (
            "Ice cream on Tuesday?",
            [],
            None,
            (timezone.now() + timedelta(days=2)).strftime("%Y-%m-%dT%H:%S.%f%Z"),
        ),
        (
            "Let's get THIS ice cream on tuesday.",
            ["8272389"],
            None,
            (timezone.now() + timedelta(days=2)).strftime("%Y-%m-%dT%H:%S.%f%Z"),
        ),
        (
            "I want to pick up that ice cream you have on Tuesday.",
            ["837837762"],
            "83761261",
            (timezone.now() + timedelta(days=2)).strftime("%Y-%m-%dT%H:%S.%f%Z"),
        ),
    ],
)
def test_send_post(
    mastodon_keyed_auth: MastodonUserAuth,
    content: str,
    media_ids: list[str],
    in_reply_to_id: str | None,
    schedule_time: datetime | None,
) -> None:
    media_attachments = []
    if media_ids is not None and len(media_ids) > 0:
        for media in media_ids:
            media_attachments.append(
                {
                    "type": "image",
                    "url": "https://files.mastodon.social/media_attachments/files/022/345/792/original/57859aede991da25.jpeg",  # noqa: E501
                    "preview_url": "https://files.mastodon.social/media_attachments/files/022/345/792/small/57859aede991da25.jpeg",  # noqa: E501
                    "remote_url": None,
                    "text_url": "https://mastodon.social/media/2N4uvkuUtPVrkZGysms",
                    "meta": {
                        "original": {
                            "width": 640,
                            "height": 480,
                            "size": "640x480",
                            "aspect": 1.3333333333333333,
                        },
                        "small": {
                            "width": 461,
                            "height": 346,
                            "size": "461x346",
                            "aspect": 1.3323699421965318,
                        },
                        "focus": {"x": -0.27, "y": 0.51},
                    },
                    "description": "test media description",
                    "blurhash": "UFBWY:8_0Jxv4mx]t8t64.%M-:IUWGWAt6M}",
                }
            )
    if schedule_time is not None:
        response_json = {
            "id": "103270115826048975",
            "scheduled_at": schedule_time.strftime("%Y-%m-%dT%H:%M:%S.%f%Z"),
            "params": {
                "text": f"{content}",
                "media_ids": media_ids,
                "sensitive": None,
                "spoiler_text": None,
                "visibility": None,
                "scheduled_at": None,
                "poll": None,
                "idempotency": None,
                "in_reply_to_id": None,
                "application_id": 596551,
            },
            "media_attachments": media_attachments,
        }
        if in_reply_to_id is not None:
            response_json["params"]["in_reply_to_id"] = in_reply_to_id  # type: ignore
    else:
        response_json = {
            "id": "103270115826048975",
            "created_at": "2019-12-08T03:48:33.901Z",
            "in_reply_to_id": None,  # type: ignore
            "in_reply_to_account_id": None,  # type: ignore
            "sensitive": False,  # type: ignore
            "spoiler_text": "",
            "visibility": "public",
            "language": "en",
            "uri": f"https://{mastodon_keyed_auth.instance.api_base_url}/users/{mastodon_keyed_auth.account_username}/statuses/103270115826048975",  # noqa: E501
            "url": f"https://{mastodon_keyed_auth.instance.api_base_url}/@{mastodon_keyed_auth.account_username}/103270115826048975",  # noqa: E501
            "replies_count": 5,  # type: ignore
            "reblogs_count": 6,  # type: ignore
            "favourites_count": 11,  # type: ignore
            "favourited": False,  # type: ignore
            "reblogged": False,  # type: ignore
            "muted": False,  # type: ignore
            "bookmarked": False,  # type: ignore
            "content": f"<p>{content}</p>",
            "reblog": None,  # type: ignore
            "application": {"name": "Web", "website": None},
            "account": {
                "id": "1",
                "username": f"{mastodon_keyed_auth.account_username}",
                "acct": f"{mastodon_keyed_auth.account_username}",
                "display_name": "Someone",
                "locked": False,
                "bot": False,
                "discoverable": True,
                "group": False,
                "created_at": "2016-03-16T14:34:26.392Z",
                "note": "<p>Someone who posts stuff</p>",
                "url": f"https://{mastodon_keyed_auth.instance.api_base_url}/@{mastodon_keyed_auth.account_username}",
                "avatar": "https://files.mastodon.social/accounts/avatars/000/000/001/original/a0abb45b92.jpg",  # noqa: E501
                "avatar_static": "https://files.mastodon.social/accounts/avatars/000/000/001/original/abb45b92.jpg",  # noqa: E501
                "header": "https://files.mastodon.social/accounts/headers/000/000/001/original/c91b871f294ea63e.png",  # noqa: E501
                "header_static": "https://files.mastodon.social/accounts/headers/000/000/001/original/c91b871f294ea63e.png",  # noqa: E501
                "followers_count": 322930,
                "following_count": 459,
                "statuses_count": 61323,
                "last_status_at": "2019-12-10T08:14:44.811Z",
                "emojis": [],
                "fields": [],
            },
            "media_attachments": media_attachments,
            "mentions": [],
            "tags": [],
            "emojis": [],
            "card": None,  # type: ignore
            "poll": None,  # type: ignore
        }
        if in_reply_to_id is not None:
            response_json["in_reply_to_id"] = in_reply_to_id
    rsp = responses.Response(
        method="POST",
        url=f"{mastodon_keyed_auth.instance.api_base_url}/api/v1/statuses",
        status=200,
        json=response_json,
    )
    responses.add(rsp)
    remote_id, remote_url = mastodon_keyed_auth.send_post(
        content, media_ids, in_reply_to_id, schedule_time
    )
    assert remote_id == "103270115826048975"
    if schedule_time is None:
        assert (
            remote_url
            == f"https://{mastodon_keyed_auth.instance.api_base_url}/@{mastodon_keyed_auth.account_username}/103270115826048975"  # noqa: E501
        )  # noqa: E501


@pytest.mark.xfail
@pytest.mark.parametrize(
    "search_value,response_json,expected_length",
    [
        ("monkeys", {"accounts": None}, 0),
        (
            "cats",
            {
                "accounts": [
                    {
                        "id": "180744",
                        "username": "catstar",
                        "acct": "catstar@catgram.jp",
                        "display_name": "catstar",
                    },
                    {
                        "id": "214293",
                        "username": "catsareweird",
                        "acct": "catsareweird",
                        "display_name": "Cats Are Weird",
                    },
                ],
            },
            2,
        ),
    ],
)
def test_username_search(
    mastodon_keyed_auth: MastodonUserAuth,
    search_value: str,
    response_json: dict[str, Any],
    expected_length: int,
) -> None:
    resp = responses.Response(
        method="GET",
        url=f"{mastodon_keyed_auth.instance.api_base_url}/api/v2/search",
        status=200,
        json=response_json,
    )
    responses.add(resp)
    results = mastodon_keyed_auth.username_search(search_value)
    assert len(results) == expected_length
