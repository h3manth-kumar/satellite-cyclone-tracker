"""Satellite image validation, loading, and conversion utilities."""

import io
from typing import Union, Tuple, Optional
import numpy as np
from PIL import Image, UnidentifiedImageError


class ImageValidationError(ValueError):
    """Raised when an input image fails validation checks."""
    pass


ALLOWED_FORMATS = {"PNG", "JPEG", "JPG", "TIFF", "TIF", "BMP", "WEBP"}
MIN_IMAGE_DIM = 32
MAX_IMAGE_DIM = 4096


def validate_and_load_image(
    image_input: Union[bytes, io.BytesIO, str, np.ndarray, Image.Image],
    target_channels: int = 3,
) -> Image.Image:
    """
    Validates and standardizes an input image to a PIL Image.

    Args:
        image_input: Raw image bytes, file path, numpy array, or PIL Image.
        target_channels: 1 for grayscale/IR or 3 for standard RGB.

    Returns:
        Standardized PIL.Image.Image in 'RGB' or 'L' mode.

    Raises:
        ImageValidationError: If input is corrupted, empty, or fails sanity checks.
    """
    if image_input is None:
        raise ImageValidationError("Image input cannot be None.")

    img: Optional[Image.Image] = None

    if isinstance(image_input, bytes):
        if len(image_input) == 0:
            raise ImageValidationError("Image input byte buffer is empty (0 bytes).")
        try:
            img = Image.open(io.BytesIO(image_input))
            img.load()  # Verify image integrity
        except (UnidentifiedImageError, OSError) as e:
            raise ImageValidationError(f"Invalid or corrupted image data: {str(e)}") from e

    elif isinstance(image_input, io.BytesIO):
        try:
            image_input.seek(0)
            img = Image.open(image_input)
            img.load()
        except (UnidentifiedImageError, OSError) as e:
            raise ImageValidationError(f"Invalid image stream: {str(e)}") from e

    elif isinstance(image_input, str):
        try:
            img = Image.open(image_input)
            img.load()
        except FileNotFoundError:
            raise ImageValidationError(f"Image file not found at: {image_input}")
        except (UnidentifiedImageError, OSError) as e:
            raise ImageValidationError(f"Could not open image file: {str(e)}") from e

    elif isinstance(image_input, np.ndarray):
        if image_input.size == 0:
            raise ImageValidationError("Numpy image array is empty.")
        
        # Handle float arrays normalized [0, 1]
        arr = image_input
        if arr.dtype in [np.float32, np.float64]:
            if arr.max() <= 1.0 and arr.min() >= 0.0:
                arr = (arr * 255.0).astype(np.uint8)
            else:
                # Clip and scale
                arr = np.clip(arr, 0, 255).astype(np.uint8)
        
        if arr.ndim == 2:
            img = Image.fromarray(arr, mode="L")
        elif arr.ndim == 3:
            if arr.shape[2] == 1:
                img = Image.fromarray(arr[:, :, 0], mode="L")
            elif arr.shape[2] in (3, 4):
                img = Image.fromarray(arr[:, :, :3], mode="RGB")
            else:
                raise ImageValidationError(f"Unsupported number of channels in array: {arr.shape[2]}")
        else:
            raise ImageValidationError(f"Unsupported array dimensions: {arr.ndim}")

    elif isinstance(image_input, Image.Image):
        img = image_input.copy()

    else:
        raise ImageValidationError(f"Unsupported input type: {type(image_input).__name__}")

    # Dimensional validation
    w, h = img.size
    if w < MIN_IMAGE_DIM or h < MIN_IMAGE_DIM:
        raise ImageValidationError(f"Image dimensions ({w}x{h}) are smaller than minimum allowed ({MIN_IMAGE_DIM}x{MIN_IMAGE_DIM}).")
    if w > MAX_IMAGE_DIM or h > MAX_IMAGE_DIM:
        raise ImageValidationError(f"Image dimensions ({w}x{h}) exceed maximum allowed ({MAX_IMAGE_DIM}x{MAX_IMAGE_DIM}).")

    # Format standardization
    if target_channels == 1:
        if img.mode != "L":
            img = img.convert("L")
    elif target_channels == 3:
        if img.mode != "RGB":
            img = img.convert("RGB")
    else:
        raise ValueError(f"target_channels must be 1 or 3, got {target_channels}")

    return img
