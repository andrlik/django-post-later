# Add any receivers for signals here.
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Account, MastodonUserAuth


@receiver(post_save, sender=MastodonUserAuth)
def update_status_for_account_object(sender, instance, created, *args, **kwargs):
    """
    When the MastodonUserAuth object is saved, check to see if it is fully ready and update
    the associated Account object accordingly.
    """
    assoc_account = instance.social_account
    if (
        instance.is_ready_post
        and assoc_account.account_status == Account.AccountStatus.PENDING
    ):
        assoc_account.account_status = Account.AccountStatus.ACTIVE
        assoc_account.save()
