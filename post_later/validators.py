from decimal import Decimal

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_focal_field_limit(value):
    """
    Validates that the values for the focal point of the media are within
    constraints.
    """

    if value < Decimal("-1.00"):
        raise ValidationError(
            _("%(value)s is less than -1.00!"), params={"value": value}
        )
    if value > Decimal("1.00"):
        raise ValidationError(
            _("%(value)s is greater than 1.00!"), params={"value": value}
        )
