"""
Pydantic schemas for the ML Prediction API.
Strictly compatible with docs/SCHEMA.md and MEMBER2_INITIAL_PROMPT.md.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class ObservationItem(BaseModel):
    """
    Historical observation fix for a cyclone.
    """
    timestamp: datetime = Field(..., description="UTC ISO-8601 timestamp of observation")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees [-90, 90]")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees [-180, 180]")
    wind_speed: Optional[float] = Field(None, ge=0.0, le=250.0, description="Sustained surface wind in knots")
    pressure: Optional[float] = Field(None, ge=850.0, le=1050.0, description="Central pressure in hPa/mbar")


class ForecastRequest(BaseModel):
    """
    Payload sent to POST /forecast, POST /track, or POST /intensity.
    """
    cyclone_id: str = Field(..., json_schema_extra={"example": "CY001"}, description="Unique cyclone identifier")
    observations: List[ObservationItem] = Field(
        ...,
        min_length=2,
        description="Chronological list of observations (minimum 2 fixes required for motion tracking)",
    )

    @field_validator("observations")
    @classmethod
    def validate_chronological_order(cls, v: List[ObservationItem]) -> List[ObservationItem]:
        for i in range(1, len(v)):
            if v[i].timestamp <= v[i - 1].timestamp:
                raise ValueError("Observations must be strictly sorted in ascending chronological order.")
        return v


class SingleHorizonPrediction(BaseModel):
    """
    Forecast point for a specific lead time horizon.
    """
    hours: int = Field(..., description="Forecast lead time in hours (+6, +12, +24, +48)")
    target_time: datetime = Field(..., description="Projected target timestamp in UTC")
    latitude: float = Field(..., description="Predicted latitude coordinate")
    longitude: float = Field(..., description="Predicted longitude coordinate")
    predicted_wind_speed: Optional[float] = Field(None, description="Predicted wind speed (knots)")
    predicted_pressure: Optional[float] = Field(None, description="Predicted central pressure (hPa)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Calibrated confidence score [0.0 - 1.0]")
    error_radius_km: float = Field(..., description="95% error cone radius in kilometers")


class ModelInfo(BaseModel):
    name: str = Field(default="CycloneTrackGRU")
    version: str = Field(default="track-model-v1.0")


class ForecastResponse(BaseModel):
    """
    Standard forecast response conforming to Member 2 contract.
    """
    cyclone_id: str = Field(...)
    forecast_time: datetime = Field(..., description="Origin timestamp of the forecast (time of latest observation)")
    predictions: List[SingleHorizonPrediction] = Field(...)
    model: ModelInfo = Field(default_factory=ModelInfo)


class TrackPredictionItem(BaseModel):
    hours: int
    target_time: datetime
    latitude: float
    longitude: float
    confidence: float
    error_radius_km: float


class TrackResponse(BaseModel):
    cyclone_id: str
    forecast_time: datetime
    predictions: List[TrackPredictionItem]
    model: ModelInfo = Field(default_factory=ModelInfo)


class IntensityPredictionItem(BaseModel):
    hours: int
    target_time: datetime
    predicted_wind_speed: Optional[float]
    predicted_pressure: Optional[float]
    confidence: float


class IntensityResponse(BaseModel):
    cyclone_id: str
    forecast_time: datetime
    predictions: List[IntensityPredictionItem]
    model: ModelInfo = Field(default_factory=ModelInfo)


class HealthResponse(BaseModel):
    status: str = Field(default="ok")
    service: str = Field(default="ml-prediction")
    model_version: str = Field(default="track-model-v1.0")
    device: str = Field(default="cpu")
