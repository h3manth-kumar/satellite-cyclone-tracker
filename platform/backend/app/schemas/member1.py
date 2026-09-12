"""Member 1 Detection and Classification integration contracts."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any


class DetectionRequest(BaseModel):
    image_id: Optional[str] = None
    image_path: Optional[str] = None
    sensor: Optional[str] = "TIR1"
    bbox: Optional[Dict[str, float]] = None


class DetectionResponse(BaseModel):
    detected: bool
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    confidence: float
    bbox: Optional[List[float]] = Field(default=None, description="[min_lat, min_lon, max_lat, max_lon]")
    pixel_center: Optional[Dict[str, int]] = None
    normalized_center: Optional[Dict[str, float]] = None
    model_version: str = "v1.0.0"
    timestamp: Optional[str] = None


class ClassificationRequest(BaseModel):
    image_id: Optional[str] = None
    image_path: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    bbox: Optional[Dict[str, float]] = None


class ClassificationResponse(BaseModel):
    classification: str
    confidence: float
    estimated_wind_speed: Optional[float] = None
    probabilities: Optional[Dict[str, float]] = None
    model_version: str = "v1.0.0"
    explainability_heatmap_path: Optional[str] = None
    explainability_heatmap_base64: Optional[str] = None
    timestamp: Optional[str] = None
