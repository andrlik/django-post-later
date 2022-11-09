import pytest
from django.contrib.auth import get_user_model

from post_later.models.mastodon import MastodonInstanceClient
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
