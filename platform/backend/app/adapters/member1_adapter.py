"""Concrete Member 1 service adapters: HTTP microservice client and resilient Mock."""

import os
import io
import json
import time
import httpx
from datetime import datetime, timezone
from typing import Optional, Tuple
from PIL import Image

from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import MLServiceUnavailableException
from app.adapters.base import IMember1Adapter
from app.schemas.common import ServiceStatus
from app.schemas.member1 import (
    DetectionRequest,
    DetectionResponse,
    ClassificationRequest,
    ClassificationResponse,
)

# Standard IMD wind speeds (knots) for intensity stages
IMD_STAGE_WIND_MAP = {
    "No Cyclone / Non-Depression": 15.0,
    "Depression": 22.0,
    "Deep Depression": 30.0,
    "Cyclonic Storm": 40.0,
    "Severe Cyclonic Storm": 55.0,
    "Very Severe Cyclonic Storm": 75.0,
    "Extremely Severe Cyclonic Storm": 105.0,
    "Super Cyclonic Storm": 130.0,
}


def _load_image_bytes(image_path: Optional[str]) -> bytes:
    """Reads image file from disk or generates a standard test image buffer."""
    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as f:
            return f.read()

    # Search common satellite storage directories
    if image_path:
        alt_paths = [
            os.path.join(settings.SATELLITE_DATA_DIR, os.path.basename(image_path)),
            os.path.join("data/satellite/raw", os.path.basename(image_path)),
            os.path.join("test_data/satellite/raw", os.path.basename(image_path)),
        ]
        for p in alt_paths:
            if os.path.exists(p):
                with open(p, "rb") as f:
                    return f.read()

    # Fallback to generating a synthetic satellite frame
    img = Image.new("RGB", (224, 224), color=(110, 130, 150))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class HttpMember1Adapter(IMember1Adapter):
    """HTTP Client connecting to Member 1 microservice (ml-detection:8001)."""

    def __init__(self, base_url: str = settings.MEMBER1_URL, timeout: float = settings.ML_TIMEOUT_SECONDS):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def check_health(self) -> ServiceStatus:
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{self.base_url}/health")
                latency_ms = round((time.time() - start_time) * 1000, 2)
                if resp.status_code == 200:
                    return ServiceStatus(status="online", url=self.base_url, latency_ms=latency_ms)
                else:
                    return ServiceStatus(status="degraded", url=self.base_url, latency_ms=latency_ms, error=f"HTTP {resp.status_code}")
        except Exception as exc:
            return ServiceStatus(status="offline", url=self.base_url, error=str(exc))

    async def detect(self, request: DetectionRequest) -> DetectionResponse:
        try:
            image_bytes = _load_image_bytes(request.image_path)
            files = {"image": ("satellite.png", image_bytes, "image/png")}
            data = {}
            if request.bbox:
                data["bbox"] = json.dumps(request.bbox)

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(f"{self.base_url}/detect", files=files, data=data)
                if resp.status_code != 200:
                    raise MLServiceUnavailableException("Member 1 Detection", f"HTTP {resp.status_code}: {resp.text}")
                res_data = resp.json()

                bbox_list = None
                if request.bbox:
                    bbox_list = [
                        request.bbox.get("min_lat", 0.0),
                        request.bbox.get("min_lon", 0.0),
                        request.bbox.get("max_lat", 0.0),
                        request.bbox.get("max_lon", 0.0),
                    ]

                return DetectionResponse(
                    detected=res_data.get("detected", True),
                    latitude=res_data.get("latitude"),
                    longitude=res_data.get("longitude"),
                    confidence=res_data.get("confidence", 0.9),
                    bbox=bbox_list,
                    pixel_center=res_data.get("pixel_center"),
                    normalized_center=res_data.get("normalized_center"),
                    model_version=res_data.get("model_version", "v1.0.0"),
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            logger.error(f"Member 1 Detection unreachable at {self.base_url}: {exc}")
            raise MLServiceUnavailableException("Member 1 Detection", str(exc))

    async def classify(self, request: ClassificationRequest) -> ClassificationResponse:
        try:
            image_bytes = _load_image_bytes(request.image_path)
            files = {"image": ("satellite.png", image_bytes, "image/png")}
            data = {}
            if request.bbox:
                data["bbox"] = json.dumps(request.bbox)

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/predict?include_explainability=true",
                    files=files,
                    data=data,
                )
                if resp.status_code != 200:
                    raise MLServiceUnavailableException("Member 1 Classification", f"HTTP {resp.status_code}: {resp.text}")
                res_data = resp.json()

                cls_info = res_data.get("classification", {})
                pred_class = cls_info.get("class", "Cyclonic Storm")
                confidence = cls_info.get("confidence", 0.85)
                probabilities = cls_info.get("probabilities", {})
                explain_info = res_data.get("explainability", {})
                heatmap_b64 = explain_info.get("heatmap_base64")
                model_meta = res_data.get("model", {})
                model_version = model_meta.get("classification_version", "v1.0.0")

                est_wind = IMD_STAGE_WIND_MAP.get(pred_class, 55.0)

                return ClassificationResponse(
                    classification=pred_class,
                    confidence=confidence,
                    estimated_wind_speed=est_wind,
                    probabilities=probabilities,
                    model_version=model_version,
                    explainability_heatmap_base64=heatmap_b64,
                    explainability_heatmap_path=None,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            logger.error(f"Member 1 Classification unreachable at {self.base_url}: {exc}")
            raise MLServiceUnavailableException("Member 1 Classification", str(exc))


class MockMember1Adapter(IMember1Adapter):
    """Resilient Mock Adapter delivering high-fidelity realistic responses for testing/offline use."""

    async def check_health(self) -> ServiceStatus:
        return ServiceStatus(status="online", url="mock://member1", latency_ms=2.5)

    async def detect(self, request: DetectionRequest) -> DetectionResponse:
        return DetectionResponse(
            detected=True,
            latitude=17.2,
            longitude=87.3,
            confidence=0.945,
            bbox=[15.0, 85.0, 19.5, 89.6],
            model_version="m1-yolov8-simulated-v1.0",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    async def classify(self, request: ClassificationRequest) -> ClassificationResponse:
        return ClassificationResponse(
            classification="Very Severe Cyclonic Storm",
            confidence=0.887,
            estimated_wind_speed=78.0,
            probabilities={
                "Depression": 0.01,
                "Deep Depression": 0.02,
                "Cyclonic Storm": 0.05,
                "Severe Cyclonic Storm": 0.12,
                "Very Severe Cyclonic Storm": 0.76,
                "Extremely Severe Cyclonic Storm": 0.04,
            },
            model_version="m1-resnet50-simulated-v1.0",
            explainability_heatmap_path="/app/data/satellite/explainability/exp_latest.png",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
