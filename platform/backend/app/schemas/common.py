"""
Common Pydantic schemas: Health, Error, and GeoJSON structures.
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime

class ServiceStatus(BaseModel):
    status: str = Field(..., description="'online', 'degraded', or 'offline'")
    url: Optional[str] = None
    latency_ms: Optional[float] = None
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str = Field(..., description="'healthy', 'degraded', or 'unhealthy'")
    timestamp: datetime
    version: str
    database: Dict[str, Any]
    services: Dict[str, ServiceStatus]

class GeoJSONGeometry(BaseModel):
    type: str # "Point", "LineString", "Polygon", "MultiPoint"
    coordinates: Any

class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    geometry: GeoJSONGeometry
    properties: Dict[str, Any]

class GeoJSONFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: List[GeoJSONFeature]
