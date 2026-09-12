"""
Unified analysis schemas for full pipeline execution.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.schemas.member1 import DetectionResponse, ClassificationResponse
from app.schemas.member2 import ForecastPoint

class FullAnalysisRequest(BaseModel):
    cyclone_id: str
    satellite_image_id: Optional[str] = None
    persist_results: bool = True

class UnifiedAnalysisResponse(BaseModel):
    timestamp: str
    status: str = Field(..., description="'success', 'partial_success', or 'failed'")
    cyclone: Dict[str, Any]
    observation: Optional[Dict[str, Any]] = None
    detection: Optional[DetectionResponse] = None
    classification: Optional[ClassificationResponse] = None
    forecast: List[ForecastPoint] = []
    models: Dict[str, str] = {}
    warnings: List[str] = []
    disclaimer: str = (
        "AI/ML Research Prototype & Decision Support Tool. "
        "Strictly for demonstration and evaluation. Not an official meteorological warning from IMD/MoES."
    )
