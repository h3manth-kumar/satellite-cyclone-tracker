"""
Observation schemas. Strictly representing observed ground-truth or sensor readings.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class ObservationBase(BaseModel):
    cyclone_id: str
    timestamp: datetime
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    wind_speed: Optional[float] = Field(default=None, description="Max sustained surface wind in Knots")
    pressure: Optional[float] = Field(default=None, description="Estimated central barometric pressure in hPa")
    classification: Optional[str] = Field(default=None, description="Official IMD intensity classification")
    source: str = Field(default="IMD_OFFICIAL", description="e.g. 'IMD_OFFICIAL', 'BUOY', 'SCAT'")

class ObservationCreate(ObservationBase):
    pass

from uuid import UUID

class ObservationResponse(ObservationBase):
    id: UUID | str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
