from __future__ import annotations

from io import BytesIO

import httpx
import pytest
from django.contrib.auth.models import AbstractBaseUser
from django.db import IntegrityError
from respx.router import MockRouter

from post_later.models.mastodon import (
    MastodonAvatar,
    MastodonInstanceClient,
    MastodonUserAuth,
    mastodon_account_directory_path,
)
from post_later.models.social_accounts import Account
from post_later.rules import is_mastodon_avatar_owner

from .factories.users import UserFactory

# from django.utils import timezone


User = AbstractBaseUser

pytestmark = pytest.mark.django_db(transaction=True)


def test_only_create_unique_clients(mastodon_client: MastodonInstanceClient) -> None:
    instance_url = mastodon_client.api_base_url
    with pytest.raises(IntegrityError):
        MastodonInstanceClient.objects.create(
            api_base_url=instance_url,
            client_id="jdkjfdhjuiwejhf8w9yue498y",
            client_secret="kdjfodjdfj89Y*Y(*YH*(UOU",
            vapid_key=None,
        )


@pytest.mark.parametrize(
    "client_id,client_secret,expected_result",
    [
        (None, None, False),
        ("jdkjfdhjuiwejhf8w9yue498y", None, False),
        (None, "kdjfodjdfj89Y*Y(*YH*(UOU", False),
        ("jdkjfdhjuiwejhf8w9yue498y", "kdjfodjdfj89Y*Y(*YH*(UOU", True),
    ],
)
def test_ready_property_for_client(
    client_id: str | None, client_secret: str | None, expected_result: bool
) -> None:
    api_base_url = "https://mastodon.social"
    mclient = MastodonInstanceClient.objects.create(
        api_base_url=api_base_url, client_id=client_id, client_secret=client_secret
    )
    assert mclient.ready is expected_result


@pytest.mark.parametrize(
    "user_key,account_username,user_secret,expected_result",
    [
        (None, None, None, False),
        ("jdfijfj8eruj8Jf8uf&*&*^^^", None, None, False),
        (None, "jeremy", "jdkjfsdjfidjfoidjh‡ﬂ*(&(&&", False),
        ("jdkjfksjhfdjhiujhfioejj(*&", "jeremy", None, False),
        (None, "jeremy", None, False),
        (None, None, "jdkfljsdfiufjhd&*^&&*^*&^&*()", False),
        (
            "jklfdjlksdjlksdjlksdjfsdj&*(&(*&(&",
            None,
            "jdflkjsdfjdiojhfoiuhydfy*&(&(",
            False,
        ),
        (
            "jdkjsdfjdsijfiouyY(**&*&^&^&",
            "jeremy",
            "kdjkjsdfjdsiiUY*(&^&^&*^%&*^",
            True,
        ),
    ],
)
def test_validity_check(
    mastodon_client: MastodonInstanceClient,
    user: User,
    user_key: str | None,
    account_username: str | None,
    user_secret: str | None,
    expected_result: bool,
) -> None:
    social_account = Account.objects.create(user=user)  # type: ignore
    mua = MastodonUserAuth.objects.create(
        instance_client=mastodon_client,
        user=user,
        user_oauth_key=user_key,
        account_username=account_username,
        user_auth_token=user_secret,
        social_account=social_account,
    )  # type: ignore
    assert mua.is_ready_post == expected_result


def test_upload_dir(mastodon_client: MastodonInstanceClient, user: User) -> None:
    social_account = Account.objects.create(user=user)  # type: ignore
    mua = MastodonUserAuth.objects.create(
        instance_client=mastodon_client,
        user=user,
        user_oauth_key="jdkljdslkjf&U*&(*^&^*(^",
        user_auth_token="jfdlkjdsfiuUY&*(&*(^(",
        account_username="jeremy",
        social_account=social_account,
    )  # type: ignore
    avatar = MastodonAvatar.objects.create(user_account=mua)
    expected_string = f"avatars/mastodon/account_{mua.id}/IMG_008.jpeg"
    assert mastodon_account_directory_path(avatar, "IMG_008.jpeg") == expected_string


def test_no_cached_avatar(mastodon_uncached_avatar: MastodonAvatar) -> None:
    assert mastodon_uncached_avatar.img_url == mastodon_uncached_avatar.source_url


def test_cached_avatar(mastodon_cached_avatar: MastodonAvatar) -> None:
    assert mastodon_cached_avatar.img_url != mastodon_cached_avatar.source_url


def test_predicate(user: User, mastodon_cached_avatar: MastodonAvatar) -> None:
    assert is_mastodon_avatar_owner(user, mastodon_cached_avatar)
    user2 = UserFactory()
    assert not is_mastodon_avatar_owner(user2, mastodon_cached_avatar)


def test_fetch_avatar(
    respx_mock: MockRouter, mastodon_uncached_avatar: MastodonAvatar, img_bytes: BytesIO
) -> None:
    respx_mock.get(mastodon_uncached_avatar.source_url).mock(
        return_value=httpx.Response(200, content=img_bytes.read())
    )
    mastodon_uncached_avatar.get_avatar()
    assert not mastodon_uncached_avatar.cache_stale
    assert mastodon_uncached_avatar.cached_avatar is not None
