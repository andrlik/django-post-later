# import httpx
import pytest

# import respx
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from post_later.models.mastodon import (
    MastodonAvatar,
    MastodonInstanceClient,
    MastodonUserAuth,
    mastodon_account_directory_path,
)

# from django.utils import timezone


User = get_user_model()

pytestmark = pytest.mark.django_db(transaction=True)


def test_only_create_unique_clients(mastodon_client):
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
def test_ready_property_for_client(client_id, client_secret, expected_result):
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
    mastodon_client, user, user_key, account_username, user_secret, expected_result
):
    mua = MastodonUserAuth.objects.create(
        instance_client=mastodon_client,
        user=user,
        user_oauth_key=user_key,
        account_username=account_username,
        user_auth_token=user_secret,
    )
    assert mua.is_ready_post == expected_result


def test_upload_dir(mastodon_client, user):
    mua = MastodonUserAuth.objects.create(
        instance_client=mastodon_client,
        user=user,
        user_oauth_key="jdkljdslkjf&U*&(*^&^*(^",
        user_auth_token="jfdlkjdsfiuUY&*(&*(^(",
        account_username="jeremy",
    )
    avatar = MastodonAvatar.objects.create(user_account=mua)
    expected_string = f"avatars/mastodon/account_{mua.id}/IMG_008.jpeg"
    assert mastodon_account_directory_path(avatar, "IMG_008.jpeg") == expected_string
