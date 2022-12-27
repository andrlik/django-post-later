from django.urls import path  # noqa: F401

from . import views

app_name = "post_later"


urlpatterns = [
    path(
        "mastodon/add_account/",
        view=views.MastodonAccountAddView.as_view(),
        name="mastodon_add_account",
    ),
    path(
        "mastodon/handle_auth/<uuid:id>/",
        view=views.HandleMastodonAuthView.as_view(),
        name="mastodon_handle_auth",
    ),
    path(
        "mastodon/accounts/",
        view=views.MastodonAccountListView.as_view(),
        name="mastodon_account_list",
    ),
    path(
        "mastodon/accounts/<uuid:id>/",
        view=views.MastodonAccountDetailView.as_view(),
        name="mastodon_account_detail",
    ),
    path(
        "mastodon/accounts/<uuid:id>/authorize/",
        view=views.MastodonLoginView.as_view(),
        name="mastodon_account_login",
    ),
    path(
        "mastodon/accounts/<uuid:id>/unlink/",
        view=views.MastodonAccountDeleteView.as_view(),
        name="mastodon_account_delete",
    ),
]
