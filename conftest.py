import pytest
from django.contrib.auth import get_user_model

from post_later.models.mastodon import MastodonInstanceClient, MastodonUserAuth
from tests.factories.users import UserFactory

User = get_user_model()


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def user():
    return UserFactory()


@pytest.fixture
def mastodon_client():
    masto = MastodonInstanceClient.objects.create(
        api_base_url="https://mastodon.social",
        client_id="jdffisdjoiwejfwejf897u98794",
        client_secret="kjdfjdwoifjwejfew980ufjew9fufjjffjwie",
        vapid_key=None,
    )
    yield masto
    masto.delete()


@pytest.fixture
def mastodon_example_client():
    masto = MastodonInstanceClient.objects.create(
        api_base_url="https://example.com",
        client_id="jdffisdjoiwejfwejf897u98794",
        client_secret="kjdfjdwoifjwejfew980ufjew9fufjjffjwie",
        vapid_key=None,
    )
    yield masto
    masto.delete()


@pytest.fixture
def mastodon_pending_user_auth(user, mastodon_example_client):
    user_auth = MastodonUserAuth.objects.create(
        instance_client=mastodon_example_client, user=user
    )
    yield user_auth
    user_auth.delete()


@pytest.fixture
def mastodon_keyed_auth(mastodon_pending_user_auth):
    mastodon_pending_user_auth.user_oauth_key = "Yzk5ZDczMzRlNDEwY"
    mastodon_pending_user_auth.save()
    yield mastodon_pending_user_auth


@pytest.fixture
def mastodon_active_auth(mastodon_keyed_auth):
    mastodon_keyed_auth.user_auth_token = "ZA-Yj3aBD8U8Cm7lKUp-lm9O9BmDgdhHzDeqsY8tlL0"
    mastodon_keyed_auth.save()
    yield mastodon_keyed_auth
