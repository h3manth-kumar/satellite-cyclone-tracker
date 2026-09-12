"""Pydantic schemas for the CycloneAI ML Detection API."""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, ConfigDict


class HealthResponse(BaseModel):
    status: str = Field(default="healthy", description="Service health state")
    service: str = Field(default="ml-detection", description="Service identifier")
    version: str = Field(default="v1.0.0", description="API version")
    model_loaded: bool = Field(default=True, description="Whether ML weights are loaded in memory")
    device: str = Field(default="cpu", description="Execution device (cpu or cuda)")
    timestamp: str = Field(..., description="Current server UTC timestamp")


class PixelCoordinates(BaseModel):
    x: int = Field(..., description="X coordinate in original image pixels")
    y: int = Field(..., description="Y coordinate in original image pixels")


class NormalizedCoordinates(BaseModel):
    x: float = Field(..., description="X coordinate normalized to [0, 1]")
    y: float = Field(..., description="Y coordinate normalized to [0, 1]")


class DetectionResult(BaseModel):
    detected: bool = Field(..., description="True if tropical cyclone detected")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score [0.0, 1.0]")
    latitude: Optional[float] = Field(default=None, description="Center latitude in degrees if geo-bounds provided")
    longitude: Optional[float] = Field(default=None, description="Center longitude in degrees if geo-bounds provided")
    pixel_center: Optional[PixelCoordinates] = Field(default=None, description="Cyclone eye center in pixel coords")
    normalized_center: Optional[NormalizedCoordinates] = Field(default=None, description="Cyclone center normalized [0, 1]")


class ClassificationResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    class_: str = Field(..., alias="class", description="Predicted IMD cyclone intensity stage")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Stage confidence score [0.0, 1.0]")
    probabilities: Dict[str, float] = Field(..., description="Probability distribution across all intensity classes")


class ExplainabilityResult(BaseModel):
    available: bool = Field(..., description="True if explainability heatmap generated")
    heatmap_base64: Optional[str] = Field(default=None, description="Base64 data URI of the Grad-CAM overlaid image")
    heatmap_path: Optional[str] = Field(default=None, description="File path to saved heatmap if stored on disk")


class ModelMetadata(BaseModel):
    detection_version: str = Field(..., description="Detection model version")
    classification_version: str = Field(..., description="Classification model version")
    backbone: str = Field(..., description="Underlying neural network backbone architecture")
    weights_loaded: bool = Field(..., description="Whether trained weights are loaded")
    inference_latency_ms: float = Field(..., description="Inference execution time in milliseconds")


class FullPredictionResponse(BaseModel):
    timestamp: str = Field(..., description="Observation or analysis UTC timestamp (ISO 8601)")
    detection: DetectionResult
    classification: ClassificationResult
    explainability: ExplainabilityResult
    model: ModelMetadata


class GeoBoundingBox(BaseModel):
    min_lat: float = Field(..., ge=-90.0, le=90.0)
    max_lat: float = Field(..., ge=-90.0, le=90.0)
    min_lon: float = Field(..., ge=-180.0, le=180.0)
    max_lon: float = Field(..., ge=-180.0, le=180.0)
