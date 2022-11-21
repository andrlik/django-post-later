from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from rules.contrib.models import RulesModel

from ..rules import is_owner, is_valid_user


class OwnedModel(RulesModel):
    """
    An abstract model class that implements the basic ownership model
    and rules meta permission pattern.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text=_("The user object that owns this instance."),
    )

    class Meta:
        abstract = True
        rules_permissions = {
            "add": is_valid_user,
            "read": is_owner,
            "edit": is_owner,
            "delete": is_owner,
            "list": is_valid_user,
        }
