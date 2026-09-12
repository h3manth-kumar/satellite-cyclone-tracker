"""
Cyclone Pydantic schemas.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

class CycloneBase(BaseModel):
    id: str
    name: Optional[str] = None
    basin: str = Field(..., description="e.g. 'North Indian Ocean', 'Bay of Bengal', 'Arabian Sea'")
    start_time: datetime
    end_time: Optional[datetime] = None
    is_active: bool = True

class CycloneCreate(CycloneBase):
    pass

class CycloneResponse(CycloneBase):
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CycloneSummaryResponse(BaseModel):
    id: str
    name: Optional[str]
    basin: str
    start_time: datetime
    end_time: Optional[datetime]
    is_active: bool
    latest_lat: Optional[float] = None
    latest_lon: Optional[float] = None
    latest_wind_speed: Optional[float] = None
    latest_pressure: Optional[float] = None
    latest_classification: Optional[str] = None
    total_observations: int = 0

    model_config = ConfigDict(from_attributes=True)
