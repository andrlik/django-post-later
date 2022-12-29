from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, TemplateView
from django.views.generic.detail import SingleObjectMixin
from mastodon import Mastodon, MastodonError
from rules.contrib.views import PermissionRequiredMixin

from ..forms import LinkMastodonAccountForm
from ..models import Account, MastodonAvatar, MastodonInstanceClient, MastodonUserAuth


class MastodonAccountAddView(LoginRequiredMixin, FormView):
    """
    A view that enables users to connect another Mastodon
    account to their profile. It should take the intial values of
    the api_base_url and then get_or_create a client and start the
    OAuth Flow.

    It will attempt to create a new app on the remote instance if needed
    and store the resulting client_id and client_secret returned.

    If successful, redirects to remote instance to start OAuth
    approval by user.
    """

    form_class = LinkMastodonAccountForm
    template_name = "post_later/mastodon/link_account.html"

    def form_valid(self, form):
        """
        Uses the instance URL to create server client if needed, then proceeds to
        authorization.
        """

        url = form.cleaned_data["instance_url"]
        with transaction.atomic():
            client, created = MastodonInstanceClient.objects.get_or_create(
                api_base_url=url
            )
            new_account = Account.objects.create(user=self.request.user)  # type: ignore
            userauth = MastodonUserAuth.objects.create(
                instance_client=client,
                user=self.request.user,  # type: ignore
                social_account=new_account,
            )
            redirect_url = reverse_lazy(
                "post_later:mastodon_handle_auth", kwargs={"id": userauth.id}
            )
            if created or not client.ready:
                # This one isn't actually registered with the instance.
                client_key, client_secret = Mastodon.create_app(
                    client_name="Post Later",
                    api_base_url=url,
                    redirect_uris=redirect_url,
                )
                client.client_id = client_key
                client.client_secret = client_secret
                client.save()
        mclient = Mastodon(
            api_base_url=url,
            client_id=client.client_id,
            client_secret=client.client_secret,
        )
        return HttpResponseRedirect(
            mclient.auth_request_url(redirect_uris=redirect_url)
        )


class HandleMastodonAuthView(
    LoginRequiredMixin, PermissionRequiredMixin, SingleObjectMixin, TemplateView
):
    """
    Given the response from a Mastodon instance set the oauth key, and redirect to
    `MastodonLoginView` to finish authenticating the user.

    Displays an error message if no oauth key is returned.
    """

    model = MastodonUserAuth
    pk_url_kwarg = "id"
    select_related = ["instance_client", "mastodonavatar"]
    code: str | None = None
    context_object_name = "auth_object"
    template_name = "post_later/mastodon/mastodon_error.html"
    mastodon_error_text = None
    permission_required = "post_later.edit_mastodonuserauth"

    def dispatch(self, request, *args, **kwargs):
        """
        If code is supplied, pull it out into a property.
        """

        self.code = request.GET.get("code", None)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.code is not None:
            self.object.user_oauth_key = self.code
            self.object.user_auth_token = None
            self.object.save()
            return HttpResponseRedirect(
                reverse_lazy(
                    "post_later:mastodon_account_login", kwargs={"id": self.object.id}
                )
            )
        else:
            self.mastodon_error_text = _(
                "Your mastodon server did not return an authorization code."
            )
        return super().get(request, *args, **kwargs)


class MastodonLoginView(
    LoginRequiredMixin, PermissionRequiredMixin, SingleObjectMixin, TemplateView
):
    """
    Requests an auth token from the Mastodon instance and saves it to `MastodonUserAuth`.
    Then redirects to associated `AccountDetailView`. Otherwise, displays the error message
    received from Mastodon.
    """

    model = MastodonUserAuth
    pk_url_kwarg = "id"
    select_related = ["instance_client", "mastodonavatar"]
    auth_token = None
    template_name = "post_later/mastodon/mastodon_error.html"
    mastodon_error_text = None
    context_object_name = "userauth"
    permission_required = "post_later.edit_mastodonuserauth"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        mclient = Mastodon(
            client_id=self.object.instance_client.client_id,
            client_secret=self.object.instance_client.client_secret,
            api_base_url=self.object.instance_client.api_base_url,
        )
        try:
            access_token = mclient.log_in(code=self.object.user_oauth_key)
            self.object.user_auth_token = access_token
            mclient = Mastodon(
                access_token=self.object.user_auth_token,
                api_base_url=self.object.instance_client.api_base_url,
            )
            user_info = mclient.me()
            self.object.account_username = user_info["acct"]
            self.object.account_url = user_info["url"]
            self.object.save()
            avatar, created = MastodonAvatar.objects.get_or_create(
                user_account=self.object
            )
            if created or avatar.source_url != user_info["avatar_static"]:
                avatar.source_url = user_info["avatar_static"]
                avatar.cache_stale = True
                avatar.save()
            return HttpResponseRedirect(
                reverse_lazy(
                    "post_later:account_detail",
                    kwargs={"id": self.object.social_account.id},
                )
            )
        except MastodonError as eme:
            self.mastodon_error_text = f"Mastodon Error: {eme}"
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        Add mastodon error message to context data if login fails.
        """

        context = super().get_context_data(**kwargs)
        context["mastodon_error"] = self.mastodon_error_text
        return context
