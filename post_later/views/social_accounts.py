from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, FormView, ListView
from django.views.generic.edit import DeleteView
from rules.contrib.views import PermissionRequiredMixin

from ..forms import AccountCreateForm
from ..models import Account


class AccountListView(LoginRequiredMixin, ListView):
    """
    Displays the list of accounts associated with the account.
    Can also be filtered additionally with GET params such as
    `type=mastodon`.
    """

    model = Account
    pk_url_kwarg = "id"
    template_name = "post_later/account_list.html"
    select_related = ["stats"]
    paginate_by = 25
    context_object_name = "accounts"
    ordering = ["created"]

    def get_queryset(self):
        """
        Return a queryset filtered to the current user and by type if
        in query string.
        """

        get_params = self.request.GET.copy()
        type_filter = get_params.get("account_type", None)
        queryset = self.model.objects.filter(user=self.request.user)  # type: ignore
        if type_filter:
            queryset = queryset.filter(account_type=type_filter)
        return queryset


class AccountCreateView(LoginRequiredMixin, FormView):
    """
    Initial view to use when creating an account link.
    """

    form_class = AccountCreateForm
    template_name = "post_later/account_create.html"

    def form_valid(self, form):
        """
        Use the type to direct the next step accordingly.
        """
        type_to_use = form.cleaned_data["account_type"]
        return HttpResponseRedirect(
            reverse_lazy(f"post_later:{type_to_use}_add_account")
        )


class AccountDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """
    View that shows the detail of a created account, including status, statistics, and associated
    data from the linked auth object associated with the service.
    """

    model = Account
    pk_url_kwarg = "id"
    context_object_name = "account"
    select_related = ["stats"]
    template_name = "post_later/account_detail.html"
    permission_required = "post_later.read_account"


class AccountDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    View for deleting an existing account.
    """

    model = Account
    pk_url_kwarg = "id"
    context_object_name = "account"
    permission_required = "post_later.delete_account"
    template_name = "post_later/account_delete.html"
    object: Account

    def get_success_url(self):
        messages.success(self.request, _("Successfully deleted account."))  # type: ignore
        return reverse_lazy("post_later:account_list")
