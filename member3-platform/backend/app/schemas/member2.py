"""Member 2 Trajectory & Intensity Forecasting integration contracts."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ObservationStep(BaseModel):
    timestamp: str = Field(..., description="UTC ISO-8601 timestamp")
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    wind_speed: Optional[float] = None
    pressure: Optional[float] = None


class ForecastRequest(BaseModel):
    cyclone_id: str
    observations: Optional[List[ObservationStep]] = None
    history: Optional[List[ObservationStep]] = None

    def model_post_init(self, __context):
        if not self.observations and self.history:
            self.observations = self.history
        if not self.observations:
            raise ValueError("Either observations or history must be provided and not empty.")


class ForecastPoint(BaseModel):
    lead_hours: int
    target_time: str
    latitude: float
    longitude: float
    predicted_wind_speed: Optional[float] = None
    predicted_pressure: Optional[float] = None
    uncertainty_radius_km: float
    confidence: float


class ForecastResponse(BaseModel):
    cyclone_id: str
    forecast_time: str
    model_version: str = "track-model-v1.0"
    forecast_points: List[ForecastPoint]
