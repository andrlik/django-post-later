import pytest
from django.core.exceptions import ValidationError

from post_later.validators import validate_focal_field_limit


@pytest.mark.parametrize(
    "input,raise_error",
    [
        (0.54, False),
        (1.00, False),
        (-0.42, False),
        (1.5, True),
        (-1.1, True),
        (-5, True),
        (5, True),
    ],
)
def test_focal_length_validator(input, raise_error):
    if raise_error:
        with pytest.raises(ValidationError):
            validate_focal_field_limit(input)
    else:
        assert validate_focal_field_limit(input) is None
