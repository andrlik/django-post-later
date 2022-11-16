from __future__ import annotations

from typing import Callable

import pytest
import responses
from django.contrib.auth.models import AbstractBaseUser
from django.core.exceptions import ObjectDoesNotExist
from django.test import Client
from django.urls import reverse

from post_later.models.mastodon import MastodonInstanceClient, MastodonUserAuth

from .factories.users import UserFactory

pytestmark = pytest.mark.django_db(transaction=True)

User = AbstractBaseUser


@pytest.mark.parametrize(
    "use_user,expected_response",
    [
        (False, 302),
        (True, 200),
    ],
)
def test_account_get_add_view_requires_login(
    client: Client,
    user: User,
    django_assert_max_num_queries: Callable,
    use_user: bool,
    expected_response: int,
) -> None:
    url = reverse("post_later:mastodon_add_account")
    if use_user:
        client.force_login(user=user)
    with django_assert_max_num_queries(50):
        response = client.get(url)
    assert response.status_code == expected_response
    if expected_response == 200:
        assert "form" in response.context.keys()
        content = response.content.decode(response.charset)
        print(content)
        assert reverse("post_later:mastodon_account_list") in response.content.decode(
            response.charset
        )
    if expected_response == 302:
        assert "accounts/login" in response["Location"]


@responses.activate
@pytest.mark.parametrize(
    "logged_in,url_to_submit,should_create,expected_response_code,expected_response_location",
    [
        (False, "https://example.com", 0, 302, "accounts/login"),
        (True, "https://mastodon.social", 0, 302, "mastodon.social/oauth"),
        (True, "https://example.com", 1, 302, "example.com/oauth"),
        (True, "848ferjdf8few", 0, 200, None),
    ],
)
def test_account_add_view(
    mastodon_client: MastodonInstanceClient,
    client: Client,
    user: User,
    django_assert_max_num_queries: Callable,
    logged_in: bool,
    url_to_submit: str | None,
    should_create: int,
    expected_response_code: int,
    expected_response_location: str | None,
) -> None:
    if logged_in:
        client.force_login(user=user)
    url = reverse("post_later:mastodon_add_account")
    current_client_count = MastodonInstanceClient.objects.count()
    if should_create > 0:
        rsp1 = responses.Response(
            method="POST",
            url=f"{url_to_submit}/api/v1/apps",
            json={
                "id": "83747329",
                "name": "Post Later",
                "redirect_uri": url,
                "website": None,
                "vapid_key": "jdfkljsdlkjfsdiuuy89798797",
                "client_id": "jdkfljdslkds8U(*&*(^(^(*",
                "client_secret": "U*(#FJHJH*F(Y(&*Y^&JIOUUY",
            },
            status=200,
        )
        responses.add(rsp1)
    with django_assert_max_num_queries(50):
        response = client.post(url, data={"instance_url": url_to_submit})
    assert (
        MastodonInstanceClient.objects.count() == current_client_count + should_create
    )
    assert response.status_code == expected_response_code
    if expected_response_location is not None:
        assert expected_response_location in response["Location"]


@pytest.mark.parametrize(
    "logged_in,correct_user,code,expected_response_code,expected_response_location,should_complete",
    [
        (False, False, None, 302, "accounts/login", False),
        (
            True,
            False,
            None,
            403,
            None,
            False,
        ),
        (True, True, None, 200, None, False),
        (True, True, "Yzk5ZDczMzRlNDEwY", 302, None, True),
    ],
)
def test_mastodon_get_oauth_code(
    user: User,
    mastodon_pending_user_auth: MastodonUserAuth,
    client: Client,
    django_assert_max_num_queries: Callable,
    logged_in: bool,
    correct_user: bool,
    code: str | None,
    expected_response_code: int,
    expected_response_location: str | None,
    should_complete: bool,
) -> None:
    test_url = reverse(
        "post_later:mastodon_handle_auth",
        kwargs={"id": mastodon_pending_user_auth.id},
    )
    if code is not None:
        test_url = test_url + f"?code={code}"
    if expected_response_location is None:
        if expected_response_code == 200:
            expected_response_location = reverse(
                "post_later:mastodon_handle_auth",
                kwargs={"id": mastodon_pending_user_auth.id},
            )
        else:
            expected_response_location = reverse(
                "post_later:mastodon_account_login",
                kwargs={"id": mastodon_pending_user_auth.id},
            )
    if logged_in:
        if correct_user:
            client.force_login(user=user)
        else:
            client.force_login(user=UserFactory())
    with django_assert_max_num_queries(50):
        response = client.get(test_url)
    assert response.status_code == expected_response_code
    if expected_response_code == 302:
        assert expected_response_location in response["Location"]
    check_value = MastodonUserAuth.objects.get(pk=mastodon_pending_user_auth.pk)
    if should_complete:
        assert check_value.user_oauth_key is not None


@responses.activate
@pytest.mark.parametrize(
    "logged_in,correct_user,auth_token,expected_response_code,expected_response_location,should_complete",
    [
        (False, False, None, 302, "accounts/login", False),
        (True, False, None, 403, None, False),
        (True, True, None, 200, None, False),
        (True, True, "ZA-Yj3aBD8U8Cm7lKUp-lm9O9BmDgdhHzDeqsY8tlL0", 302, None, True),
    ],
)
def test_mastodon_account_login(
    user: User,
    mastodon_keyed_auth: MastodonUserAuth,
    client: Client,
    django_assert_max_num_queries: Callable,
    logged_in: bool,
    correct_user: bool,
    auth_token: str | None,
    expected_response_code: int,
    expected_response_location: str | None,
    should_complete: bool,
) -> None:
    test_url = reverse(
        "post_later:mastodon_account_login", kwargs={"id": mastodon_keyed_auth.id}
    )
    if logged_in:
        if correct_user:
            client.force_login(user=user)
        else:
            client.force_login(user=UserFactory())
    if should_complete and expected_response_location is None:
        expected_response_location = reverse(
            "post_later:mastodon_account_detail", kwargs={"id": mastodon_keyed_auth.id}
        )
    if logged_in and correct_user:
        if auth_token:
            rsp = responses.Response(
                method="POST",
                url=f"{mastodon_keyed_auth.instance_client.api_base_url}/oauth/token",
                status=200,
                json={
                    "access_token": auth_token,
                    "token_type": "Bearer",
                    "scope": "read write follow push",
                    "created_at": 1573979017,
                },
            )
        else:
            rsp = rsp = responses.Response(
                method="POST",
                url=f"{mastodon_keyed_auth.instance_client.api_base_url}/oauth/token",
                status=401,
                json={
                    "error": "invalid_client",
                    "error_description": "Client authentication failed due to unknown client, no client authentication included, or unsupported authentication method.",  # noqa: F501 E501
                },
            )
        responses.add(rsp)
        if should_complete:
            rsp2 = responses.Response(
                method="GET",
                url=f"{mastodon_keyed_auth.instance_client.api_base_url}/api/v1/accounts/verify_credentials",
                status=200,
                # This output copied from the Mastodon api docs.
                json={
                    "id": "14715",
                    "username": "trwnh",
                    "acct": "trwnh",
                    "display_name": "infinite love ⴳ",
                    "locked": False,
                    "bot": False,
                    "created_at": "2016-11-24T10:02:12.085Z",
                    "note": '<p>i have approximate knowledge of many things. perpetual student. (nb/ace/they)</p><p>xmpp/email: a@trwnh.com<br /><a href="https://trwnh.com" rel="nofollow noopener noreferrer" target="_blank"><span class="invisible">https://</span><span class="">trwnh.com</span><span class="invisible"></span></a><br />help me live: <a href="https://liberapay.com/at" rel="nofollow noopener noreferrer" target="_blank"><span class="invisible">https://</span><span class="">liberapay.com/at</span><span class="invisible"></span></a> or <a href="https://paypal.me/trwnh" rel="nofollow noopener noreferrer" target="_blank"><span class="invisible">https://</span><span class="">paypal.me/trwnh</span><span class="invisible"></span></a></p><p>- my triggers are moths and glitter<br />- i have all notifs except mentions turned off, so please interact if you wanna be friends! i literally will not notice otherwise<br />- dm me if i did something wrong, so i can improve<br />- purest person on fedi, do not lewd in my presence<br />- #1 ami cole fan account</p><p>:fatyoshi:</p>',  # noqa: F501 E501
                    "url": f"https://{mastodon_keyed_auth.instance_client.api_base_url}/@trwnh",
                    "avatar": "https://files.mastodon.social/accounts/avatars/000/014/715/original/34aa222f4ae2e0a9.png",  # noqa: F501 E501
                    "avatar_static": "https://files.mastodon.social/accounts/avatars/000/014/715/original/34aa222f4ae2e0a9.png",  # noqa: F501 E501
                    "header": "https://files.mastodon.social/accounts/headers/000/014/715/original/5c6fc24edb3bb873.jpg",  # noqa: F501 E501
                    "header_static": "https://files.mastodon.social/accounts/headers/000/014/715/original/5c6fc24edb3bb873.jpg",  # noqa: F501 E501
                    "followers_count": 821,
                    "following_count": 178,
                    "statuses_count": 33120,
                    "last_status_at": "2019-11-24T15:49:42.251Z",
                    "source": {
                        "privacy": "public",
                        "sensitive": False,
                        "language": "",
                        "note": "i have approximate knowledge of many things. perpetual student. (nb/ace/they)\r\n\r\nxmpp/email: a@trwnh.com\r\nhttps://trwnh.com\r\nhelp me live: https://liberapay.com/at or https://paypal.me/trwnh\r\n\r\n- my triggers are moths and glitter\r\n- i have all notifs except mentions turned off, so please interact if you wanna be friends! i literally will not notice otherwise\r\n- dm me if i did something wrong, so i can improve\r\n- purest person on fedi, do not lewd in my presence\r\n- #1 ami cole fan account\r\n\r\n:fatyoshi:",  # noqa: F501 E501
                        "fields": [
                            {
                                "name": "Website",
                                "value": "https://trwnh.com",
                                "verified_at": "2019-08-29T04:14:55.571+00:00",
                            },
                            {
                                "name": "Sponsor",
                                "value": "https://liberapay.com/at",
                                "verified_at": "2019-11-15T10:06:15.557+00:00",
                            },
                            {
                                "name": "Fan of:",
                                "value": "Punk-rock and post-hardcore (Circa Survive, letlive., La Dispute, THE FEVER 333)Manga (Yu-Gi-Oh!, One Piece, JoJo's Bizarre Adventure, Death Note, Shaman King)Platformers and RPGs (Banjo-Kazooie, Boktai, Final Fantasy Crystal Chronicles)",  # noqa: F501 E501
                                "verified_at": None,
                            },
                            {
                                "name": "Main topics:",
                                "value": "systemic analysis, design patterns, anticapitalism, info/tech freedom, theory and philosophy, and otherwise being a genuine and decent wholesome poster. i'm just here to hang out and talk to cool people!",  # noqa: F501 E501
                                "verified_at": None,
                            },
                        ],
                        "follow_requests_count": 0,
                    },
                    "emojis": [
                        {
                            "shortcode": "fatyoshi",
                            "url": "https://files.mastodon.social/custom_emojis/images/000/023/920/original/e57ecb623faa0dc9.png",  # noqa: F501 E501
                            "static_url": "https://files.mastodon.social/custom_emojis/images/000/023/920/static/e57ecb623faa0dc9.png",  # noqa: F501 E501
                            "visible_in_picker": None,
                        }
                    ],
                    "fields": [
                        {
                            "name": "Website",
                            "value": '<a href="https://trwnh.com" rel="me nofollow noopener noreferrer" target="_blank"><span class="invisible">https://</span><span class="">trwnh.com</span><span class="invisible"></span></a>',  # noqa: F501 E501
                            "verified_at": "2019-08-29T04:14:55.571+00:00",
                        },
                        {
                            "name": "Sponsor",
                            "value": '<a href="https://liberapay.com/at" rel="me nofollow noopener noreferrer" target="_blank"><span class="invisible">https://</span><span class="">liberapay.com/at</span><span class="invisible"></span></a>',  # noqa: F501 E501
                            "verified_at": "2019-11-15T10:06:15.557+00:00",
                        },
                        {
                            "name": "Fan of:",
                            "value": "Punk-rock and post-hardcore (Circa Survive, letlive., La Dispute, THE FEVER 333)Manga (Yu-Gi-Oh!, One Piece, JoJo&apos;s Bizarre Adventure, Death Note, Shaman King)Platformers and RPGs (Banjo-Kazooie, Boktai, Final Fantasy Crystal Chronicles)",  # noqa: F501 E501
                            "verified_at": None,
                        },
                        {
                            "name": "Main topics:",
                            "value": "systemic analysis, design patterns, anticapitalism, info/tech freedom, theory and philosophy, and otherwise being a genuine and decent wholesome poster. i&apos;m just here to hang out and talk to cool people!",  # noqa: F501 E501
                            "verified_at": None,
                        },
                    ],
                },
            )
            responses.add(rsp2)
    with django_assert_max_num_queries(50):
        response = client.get(test_url)
    assert response.status_code == expected_response_code
    if expected_response_code == 302 and expected_response_location is not None:
        assert expected_response_location in response["Location"]
    check_value = MastodonUserAuth.objects.get(pk=mastodon_keyed_auth.pk)
    if should_complete:
        assert (
            check_value.user_auth_token is not None
            and check_value.user_auth_token == auth_token
        )
        assert check_value.account_username == "trwnh"
        assert (
            check_value.mastodonavatar.source_url
            == "https://files.mastodon.social/accounts/avatars/000/014/715/original/34aa222f4ae2e0a9.png"
        )
    else:
        assert check_value.user_auth_token is None


@pytest.mark.parametrize(
    "logged_in,correct_user,expected_response_code,expected_response_location",
    [
        (False, False, 302, "accounts/login"),
        (True, False, 403, None),
        (True, True, 200, None),
    ],
)
def test_account_detail_view(
    mastodon_active_auth: MastodonUserAuth,
    user: User,
    client: Client,
    django_assert_max_num_queries: Callable,
    logged_in: bool,
    correct_user: bool,
    expected_response_code: int,
    expected_response_location: str | None,
) -> None:
    if logged_in:
        if correct_user:
            client.force_login(user=user)
        else:
            client.force_login(user=UserFactory())
    test_url = reverse(
        "post_later:mastodon_account_detail", kwargs={"id": mastodon_active_auth.id}
    )
    with django_assert_max_num_queries(50):
        response = client.get(test_url)
    assert response.status_code == expected_response_code
    if expected_response_location is not None:
        assert expected_response_location in response["Location"]


@pytest.mark.parametrize(
    "logged_in,correct_user,expected_response_code,expected_response_location,expected_record_count",
    [
        (False, False, 302, "accounts/login", 0),
        (True, False, 200, None, 0),
        (True, True, 200, None, 1),
    ],
)
def test_mastodon_account_list_view(
    mastodon_active_auth: MastodonUserAuth,
    user: User,
    client: Client,
    django_assert_max_num_queries: Callable,
    logged_in: bool,
    correct_user: bool,
    expected_response_code: int,
    expected_response_location: str | None,
    expected_record_count: int,
) -> None:
    if logged_in:
        if correct_user:
            client.force_login(user=user)
        else:
            client.force_login(user=UserFactory())
    test_url = reverse("post_later:mastodon_account_list")
    with django_assert_max_num_queries(50):
        response = client.get(test_url)
    assert response.status_code == expected_response_code
    if expected_response_location is not None:
        assert expected_response_location in response["Location"]
    if expected_response_code == 200:
        assert response.context["accounts"].count() == expected_record_count


@pytest.mark.parametrize(
    "logged_in,correct_user,expected_response_code,expected_response_location",
    [
        (False, False, 302, "accounts/login"),
        (True, False, 403, None),
        (True, True, 200, None),
    ],
)
def test_mastodon_account_get_delete_view(
    mastodon_active_auth: MastodonUserAuth,
    user: User,
    client: Client,
    django_assert_max_num_queries: Callable,
    logged_in: bool,
    correct_user: bool,
    expected_response_code: int,
    expected_response_location: str | None,
) -> None:
    if logged_in:
        if correct_user:
            client.force_login(user=user)
        else:
            client.force_login(user=UserFactory())
    test_url = reverse(
        "post_later:mastodon_account_delete", kwargs={"id": mastodon_active_auth.id}
    )
    with django_assert_max_num_queries(50):
        response = client.get(test_url)
    assert response.status_code == expected_response_code
    if expected_response_location is not None:
        assert expected_response_location in response["Location"]


@pytest.mark.parametrize(
    "logged_in,correct_user,expected_response_code,expected_response_location,should_delete",
    [
        (False, False, 302, "accounts/login", False),
        (True, False, 403, None, False),
        (True, True, 302, reverse("post_later:mastodon_account_list"), True),
    ],
)
def test_mastodon_account_post_delete_view(
    mastodon_active_auth: MastodonUserAuth,
    user: User,
    client: Client,
    django_assert_max_num_queries: Callable,
    logged_in: bool,
    correct_user: bool,
    expected_response_code: int,
    expected_response_location: str | None,
    should_delete: bool,
) -> None:
    if logged_in:
        if correct_user:
            client.force_login(user=user)
        else:
            client.force_login(user=UserFactory())
    record_pk = mastodon_active_auth.id
    test_url = reverse("post_later:mastodon_account_delete", kwargs={"id": record_pk})
    with django_assert_max_num_queries(50):
        response = client.post(test_url, data={})
    assert response.status_code == expected_response_code
    if expected_response_location is not None:
        assert expected_response_location in response["Location"]
    if should_delete:
        with pytest.raises(ObjectDoesNotExist):
            MastodonUserAuth.objects.get(id=record_pk)
    else:
        assert MastodonUserAuth.objects.get(id=record_pk)
