"""Tests for image loading, preprocessing, validation, and geospatial calculations."""

import io
import pytest
import numpy as np
from PIL import Image
import torch

from src.preprocessing.image_loader import (
    validate_and_load_image,
    ImageValidationError,
    MIN_IMAGE_DIM,
    MAX_IMAGE_DIM,
)
from src.preprocessing.transforms import preprocess_for_model
from src.preprocessing.geo_utils import (
    validate_coordinates,
    pixel_to_latlon,
    latlon_to_pixel,
)


def _create_sample_image(width: int = 256, height: int = 256, mode: str = "RGB") -> bytes:
    img = Image.new(mode, (width, height), color=(128, 128, 128) if mode == "RGB" else 128)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_validate_and_load_valid_rgb():
    img_bytes = _create_sample_image(256, 256, "RGB")
    loaded = validate_and_load_image(img_bytes, target_channels=3)
    assert isinstance(loaded, Image.Image)
    assert loaded.mode == "RGB"
    assert loaded.size == (256, 256)


def test_validate_and_load_grayscale_converted_to_rgb():
    img_bytes = _create_sample_image(256, 256, "L")
    loaded = validate_and_load_image(img_bytes, target_channels=3)
    assert loaded.mode == "RGB"


def test_validate_and_load_numpy_input():
    arr = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    loaded = validate_and_load_image(arr, target_channels=3)
    assert loaded.size == (100, 100)


def test_empty_bytes_raises_error():
    with pytest.raises(ImageValidationError, match="empty"):
        validate_and_load_image(b"")


def test_corrupt_bytes_raises_error():
    with pytest.raises(ImageValidationError, match="Invalid or corrupted"):
        validate_and_load_image(b"not-a-valid-image-stream-bytes")


def test_too_small_image_raises_error():
    small_bytes = _create_sample_image(MIN_IMAGE_DIM - 10, MIN_IMAGE_DIM - 10)
    with pytest.raises(ImageValidationError, match="smaller than minimum"):
        validate_and_load_image(small_bytes)


def test_preprocess_for_model_tensor_shape():
    img_bytes = _create_sample_image(300, 300)
    pil_img = validate_and_load_image(img_bytes)
    tensor = preprocess_for_model(pil_img, target_size=(224, 224), channels=3)

    assert isinstance(tensor, torch.Tensor)
    assert tensor.shape == (1, 3, 224, 224)
    assert not torch.isnan(tensor).any()
    assert not torch.isinf(tensor).any()


def test_coordinate_validation():
    assert validate_coordinates(15.5, 85.0) is True
    assert validate_coordinates(-90.0, -180.0) is True
    assert validate_coordinates(90.0, 180.0) is True
    assert validate_coordinates(95.0, 50.0) is False  # Lat out of range
    assert validate_coordinates(20.0, 200.0) is False  # Lon out of range


def test_pixel_to_latlon_mapping():
    bbox = {
        "min_lat": 10.0,
        "max_lat": 20.0,
        "min_lon": 80.0,
        "max_lon": 90.0,
    }
    # Center of 100x100 image should be (15.0, 85.0)
    lat, lon = pixel_to_latlon(50, 50, 100, 100, bbox=bbox)
    assert lat == 15.0
    assert lon == 85.0

    # Top-left (0, 0) is max_lat (20.0), min_lon (80.0)
    lat_tl, lon_tl = pixel_to_latlon(0, 0, 100, 100, bbox=bbox)
    assert lat_tl == 20.0
    assert lon_tl == 80.0


def test_latlon_to_pixel_mapping():
    bbox = {
        "min_lat": 10.0,
        "max_lat": 20.0,
        "min_lon": 80.0,
        "max_lon": 90.0,
    }
    px, py = latlon_to_pixel(15.0, 85.0, 100, 100, bbox=bbox)
    assert px == 50
    assert py == 50
