import io

from django.core.files import File
from django.core.files.images import ImageFile
from PIL import Image, ImageOps


def resize_image(
    source_img: File, max_height: int, max_width: int, cover: bool = False
) -> ImageFile:
    """
    Given a source image `File` object resize it to the specified dimensions
    and return the resulting image as a `File` object.
    Args:
        source_img: The Django `file` object representing the image.
        max_height: int representing maximum height allowed.
        max_width: int representing maximum width allowed.
        cover: Bool representing whether to use a fit-based crop for resizing.

    Returns: File object representing the final image.

    """
    with Image.open(source_img, "r") as img:
        orig_width, orig_height = img.size
        if orig_width > max_width or orig_height > max_height:
            if cover:
                resized_image = ImageOps.fit(
                    img,
                    size=(max_width, max_height),
                    method=Image.Resampling.BILINEAR,
                )
            else:
                resized_image = img.copy()
                resized_image.thumbnail(
                    size=(max_width, max_height), resample=Image.Resampling.BILINEAR
                )
        else:
            resized_image = img.copy()
        new_bytes = io.BytesIO()
        resized_image.save(new_bytes, format=img.format)
        file = ImageFile(new_bytes, name=f"thumb_{source_img.name}")
    return file
