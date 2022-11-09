# import httpx
import pytest

# import respx
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from post_later.models.mastodon import MastodonInstanceClient

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
