"""
Satellite image metadata schemas.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

class SatelliteImageBase(BaseModel):
    id: str
    cyclone_id: Optional[str] = None
    timestamp: datetime
    satellite: str = Field(..., description="e.g. 'INSAT-3D', 'INSAT-3DR'")
    sensor: str = Field(..., description="e.g. 'IMAGER', 'SOUNDER'")
    channel: str = Field(..., description="e.g. 'TIR1', 'TIR2', 'MIR', 'VIS', 'WV'")
    file_path: str
    resolution_km: float = 4.0
    min_lat: Optional[float] = None
    min_lon: Optional[float] = None
    max_lat: Optional[float] = None
    max_lon: Optional[float] = None

class SatelliteImageCreate(SatelliteImageBase):
    pass

class SatelliteImageResponse(SatelliteImageBase):
    created_at: datetime
    download_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
