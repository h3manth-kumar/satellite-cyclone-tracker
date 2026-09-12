"""API integration tests for FastAPI service."""

import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from src.api.app import app
from src.inference.engine import CycloneInferenceEngine


@pytest.fixture(scope="module")
def client():
    # Set engine on app state for test client lifespan
    app.state.engine = CycloneInferenceEngine(device="cpu", version="v1.0.0")
    with TestClient(app) as test_client:
        yield test_client


def _get_image_bytes(width: int = 256, height: int = 256) -> bytes:
    img = Image.new("RGB", (width, height), color=(120, 140, 160))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "ml-detection"
    assert "version" in data
    assert "model_loaded" in data
    assert "timestamp" in data


def test_predict_endpoint_full(client):
    img_bytes = _get_image_bytes(256, 256)
    files = {"image": ("test_cyclone.png", img_bytes, "image/png")}
    data = {
        "bbox": '{"min_lat": 10.0, "max_lat": 25.0, "min_lon": 80.0, "max_lon": 95.0}',
        "timestamp": "2026-09-04T12:00:00Z",
    }

    response = client.post("/predict?include_explainability=true", files=files, data=data)
    assert response.status_code == 200
    res = response.json()

    # Structure checks
    assert "timestamp" in res
    assert "detection" in res
    assert "classification" in res
    assert "explainability" in res
    assert "model" in res

    assert "detected" in res["detection"]
    assert "confidence" in res["detection"]
    assert res["detection"]["latitude"] is not None
    assert res["detection"]["longitude"] is not None

    assert "class" in res["classification"]
    assert "probabilities" in res["classification"]
    assert res["explainability"]["available"] is True
    assert res["explainability"]["heatmap_base64"] is not None


def test_detect_endpoint(client):
    img_bytes = _get_image_bytes(224, 224)
    files = {"image": ("test.png", img_bytes, "image/png")}

    response = client.post("/detect", files=files)
    assert response.status_code == 200
    data = response.json()
    assert "detected" in data
    assert "confidence" in data
    assert "pixel_center" in data


def test_classify_endpoint(client):
    img_bytes = _get_image_bytes(224, 224)
    files = {"image": ("test.png", img_bytes, "image/png")}

    response = client.post("/classify", files=files)
    assert response.status_code == 200
    data = response.json()
    assert "class" in data
    assert "confidence" in data
    assert "probabilities" in data


def test_explain_endpoint(client):
    img_bytes = _get_image_bytes(224, 224)
    files = {"image": ("test.png", img_bytes, "image/png")}

    response = client.post("/explain", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["available"] is True
    assert data["heatmap_base64"] is not None


def test_invalid_corrupt_file(client):
    files = {"image": ("corrupted.png", b"invalid-bytes-stream", "image/png")}
    response = client.post("/predict", files=files)
    assert response.status_code == 422


def test_empty_file(client):
    files = {"image": ("empty.png", b"", "image/png")}
    response = client.post("/predict", files=files)
    assert response.status_code == 400
