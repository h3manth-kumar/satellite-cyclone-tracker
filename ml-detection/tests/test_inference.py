"""Tests for the end-to-end inference engine."""

import io
import pytest
from PIL import Image
from src.inference.engine import CycloneInferenceEngine
from src.training.dataset import generate_synthetic_satellite_image


@pytest.fixture
def engine():
    return CycloneInferenceEngine(device="cpu", version="v1.0.0")


def test_analyze_image_with_cyclone(engine):
    img, meta = generate_synthetic_satellite_image(size=(256, 256), has_cyclone=True, intensity_stage=3)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_bytes = buf.getvalue()

    bbox = {"min_lat": 12.0, "max_lat": 22.0, "min_lon": 82.0, "max_lon": 92.0}

    result = engine.analyze_image(
        image_input=img_bytes,
        bbox=bbox,
        include_explainability=True,
    )

    assert "timestamp" in result
    assert "detection" in result
    assert "classification" in result
    assert "explainability" in result
    assert "model" in result

    # Detection checks
    assert isinstance(result["detection"]["detected"], bool)
    assert 0.0 <= result["detection"]["confidence"] <= 1.0
    assert result["detection"]["latitude"] is not None
    assert result["detection"]["longitude"] is not None
    assert 12.0 <= result["detection"]["latitude"] <= 22.0
    assert 82.0 <= result["detection"]["longitude"] <= 92.0

    # Classification checks
    assert isinstance(result["classification"]["class"], str)
    assert 0.0 <= result["classification"]["confidence"] <= 1.0

    # Explainability checks
    assert result["explainability"]["available"] is True
    assert result["explainability"]["heatmap_base64"].startswith("data:image/png;base64,")

    # Performance
    assert result["model"]["inference_latency_ms"] > 0.0


def test_analyze_image_without_bbox(engine):
    img, _ = generate_synthetic_satellite_image(size=(224, 224), has_cyclone=False)
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    result = engine.analyze_image(
        image_input=buf.getvalue(),
        bbox=None,
        include_explainability=False,
    )

    # Coordinates must be None when no bbox is provided
    assert result["detection"]["latitude"] is None
    assert result["detection"]["longitude"] is None
    assert result["detection"]["pixel_center"] is not None


def test_missing_model_file_fallback():
    engine_missing = CycloneInferenceEngine(
        weights_path="non_existent_path_to_model.pth",
        device="cpu",
    )
    assert engine_missing.weights_loaded is False
    img, _ = generate_synthetic_satellite_image(size=(224, 224), has_cyclone=True)
    res = engine_missing.analyze_image(img, include_explainability=False)
    assert "detection" in res
    assert res["model"]["weights_loaded"] is False
