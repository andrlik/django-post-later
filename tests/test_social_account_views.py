from __future__ import annotations

from typing import Callable

import pytest
from django.contrib.auth.models import AbstractBaseUser
from django.core.exceptions import ObjectDoesNotExist
from django.test import Client
from django.urls import reverse

from post_later.models import Account, MastodonUserAuth

from .factories.users import UserFactory

pytestmark = pytest.mark.django_db(transaction=True)

User = AbstractBaseUser


@pytest.mark.parametrize(
    "view_name,is_detail_view,logged_in",
    [
        ("account_list", False, False),
        ("account_list", False, True),
        ("account_detail", True, False),
        ("account_detail", True, True),
        ("account_create", False, False),
        ("account_create", False, True),
        ("account_delete", True, False),
        ("account_delete", True, True),
    ],
)
def test_list_detail_views_require_login(
    client: Client,
    django_assert_max_num_queries: Callable,
    mastodon_keyed_auth: MastodonUserAuth,
    view_name: str,
    is_detail_view: bool,
    logged_in: bool,
) -> None:
    if is_detail_view:
        url = reverse(
            f"post_later:{view_name}",
            kwargs={"id": mastodon_keyed_auth.social_account.id},
        )
    else:
        url = reverse(f"post_later:{view_name}")
    if logged_in:
        client.force_login(user=mastodon_keyed_auth.user)
    with django_assert_max_num_queries(50):
        response = client.get(url)
    if logged_in:
        assert response.status_code == 200
    else:
        assert response.status_code == 302
        assert "accounts/login" in response["Location"]


@pytest.mark.parametrize("correct_user", [(True,), (False,)])
def test_list_view_user_specific(
    client: Client,
    django_assert_max_num_queries: Callable,
    mastodon_keyed_auth: MastodonUserAuth,
    correct_user: bool,
) -> None:
    url = reverse("post_later:account_list")
    if correct_user:
        client.force_login(user=mastodon_keyed_auth.user)
    else:
        client.force_login(user=UserFactory())
    with django_assert_max_num_queries(50):
        response = client.get(url)
    if correct_user:
        assert response.context["accounts"].count() > 0
    else:
        assert response.context["accounts"].count() == 0


@pytest.mark.parametrize(
    "view_name,correct_user",
    [
        ("account_detail", True),
        ("account_detail", False),
        ("account_delete", True),
        ("account_delete", False),
    ],
)
def test_detail_views_require_permission(
    client: Client,
    django_assert_max_num_queries: Callable,
    mastodon_keyed_auth: MastodonUserAuth,
    view_name: str,
    correct_user: bool,
) -> None:
    url = reverse(
        f"post_later:{view_name}", kwargs={"id": mastodon_keyed_auth.social_account.id}
    )
    if correct_user:
        client.force_login(user=mastodon_keyed_auth.user)
    else:
        client.force_login(user=UserFactory())
    with django_assert_max_num_queries(50):
        response = client.get(url)
    if correct_user:
        assert response.status_code == 200
    else:
        assert response.status_code == 403


@pytest.mark.parametrize(
    "logged_in, correct_user", [(False, False), (True, False), (True, True)]
)
def test_deletion_requires_permission(
    client: Client,
    django_assert_max_num_queries: Callable,
    mastodon_active_auth: MastodonUserAuth,
    logged_in: bool,
    correct_user: bool,
) -> None:
    account_id = mastodon_active_auth.social_account.id
    url = reverse("post_later:account_delete", kwargs={"id": account_id})
    if logged_in:
        if correct_user:
            client.force_login(user=mastodon_active_auth.user)
        else:
            client.force_login(user=UserFactory())
    account_totals = Account.objects.count()
    with django_assert_max_num_queries(50):
        response = client.post(url, data={})
    if not logged_in:
        assert response.status_code == 302
        assert "accounts/login" in response["Location"]
    else:
        if not correct_user:
            assert response.status_code == 403
            assert Account.objects.count() == account_totals
            assert Account.objects.get(id=account_id) is not None
        else:
            assert response.status_code == 302
            assert account_totals - Account.objects.count() == 1
            with pytest.raises(ObjectDoesNotExist):
                Account.objects.get(id=account_id)


@pytest.mark.parametrize(
    "logged_in,type_to_try,expected_status_code,expected_redirect_viewname",
    [
        (False, "mastodon", 302, None),
        (True, "mastodon", 302, "post_later:mastodon_add_account"),
        (True, "reddit", 200, None),
    ],
)
def test_account_create_enforces_types(
    client: Client,
    django_assert_max_num_queries: Callable,
    user: User,
    logged_in: bool,
    type_to_try: str,
    expected_status_code: int,
    expected_redirect_viewname: str | None,
) -> None:
    url = reverse("post_later:account_create")
    if logged_in:
        client.force_login(user=user)
    with django_assert_max_num_queries(50):
        response = client.post(url, data={"account_type": type_to_try})
    assert response.status_code == expected_status_code
    if expected_status_code == 302:
        if not logged_in:
            assert "accounts/login" in response["Location"]
        else:
            assert reverse(expected_redirect_viewname) in response["Location"]
    else:
        assert response.context["form"] is not None


@pytest.mark.parametrize(
    "type_to_filter,expected_result_count",
    [("mastodon", 1), ("twitter", 0), ("monkey", 0)],
)
def test_filtering_of_accounts(
    client: Client,
    django_assert_max_num_queries: Callable,
    mastodon_active_auth: MastodonUserAuth,
    type_to_filter: str,
    expected_result_count: int,
) -> None:
    url = f"{reverse('post_later:account_list')}?account_type={type_to_filter}"
    client.force_login(user=mastodon_active_auth.user)
    with django_assert_max_num_queries(50):
        response = client.get(url)
    assert response.status_code == 200
    assert response.context["accounts"].count() == expected_result_count


def test_pagination_loads(
    client: Client,
    django_assert_max_num_queries: Callable,
    mastodon_keyed_auth: MastodonUserAuth,
) -> None:
    url = f"{reverse('post_later:account_list')}?page=2"
    for x in range(60):
        Account.objects.create(user=mastodon_keyed_auth.user)
    client.force_login(user=mastodon_keyed_auth.user)
    with django_assert_max_num_queries(50):
        response = client.get(url)
    assert response.status_code == 200
    assert response.context["page_obj"].has_other_pages
