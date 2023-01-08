from __future__ import annotations

from io import BytesIO

import pytest
from django.core.exceptions import ValidationError
from django.core.files.images import ImageFile

from post_later.utils import resize_image
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
def test_focal_length_validator(input: float, raise_error: bool) -> None:
    if raise_error:
        with pytest.raises(ValidationError):
            validate_focal_field_limit(input)
    else:
        assert validate_focal_field_limit(input) is None


def test_resize_image_cover(img_bytes: BytesIO) -> None:
    original_image_file = ImageFile(img_bytes, name="IMG_0008.jpeg")
    orig_size = original_image_file.size
    orig_height = original_image_file.height
    orig_width = original_image_file.width
    print(
        f"Original image has a size of {orig_size}, a height of {orig_height}, and a width of {orig_width}."
    )
    new_image = resize_image(original_image_file, 200, 200, True)
    assert new_image.size < orig_size
    assert new_image.height == 200
    assert new_image.width == 200


def test_resize_image_non_cover(img_bytes: BytesIO) -> None:
    original_image_file = ImageFile(img_bytes, name="IMG_0008.jpeg")
    orig_size = original_image_file.size
    orig_height = original_image_file.height
    orig_width = original_image_file.width
    print(
        f"Original image has a size of {orig_size}, a height of {orig_height}, and a width of {orig_width}."
    )
    new_image = resize_image(original_image_file, 200, 200, False)
    print(
        f"New image has a size of {new_image.size}, a height of {new_image.height}, and a width of {new_image.width}."
    )
    assert new_image.size < orig_size
    assert new_image.height < orig_height
    assert new_image.width < orig_width


def test_resize_image_unnecessary(small_img_bytes: BytesIO) -> None:
    original_image_file = ImageFile(small_img_bytes, name="IMG_0008.jpeg")
    orig_size = original_image_file.size
    orig_height = original_image_file.height
    orig_width = original_image_file.width
    print(
        f"Original image has a size of {orig_size}, a height of {orig_height}, and a width of {orig_width}."
    )
    new_image = resize_image(original_image_file, 200, 200, False)
    print(
        f"New image has a size of {new_image.size}, a height of {new_image.height}, and a width of {new_image.width}."
    )
    assert new_image.height == orig_height
    assert new_image.width == orig_width
