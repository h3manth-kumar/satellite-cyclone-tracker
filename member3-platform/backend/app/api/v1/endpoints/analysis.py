"""
AI/ML Analysis pipeline endpoints coordinating Member 1 and Member 2 services.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from app.db.session import get_db
from app.api.deps import get_m1, get_m2
from app.adapters.base import IMember1Adapter, IMember2Adapter
from app.schemas.member1 import (
    DetectionRequest, DetectionResponse,
    ClassificationRequest, ClassificationResponse
)
from app.schemas.member2 import ForecastRequest, ForecastResponse
from app.schemas.analysis import FullAnalysisRequest, UnifiedAnalysisResponse
from app.services.analysis_orchestrator import AnalysisOrchestrator
from app.core.exceptions import CycloneNotFoundException, MLServiceUnavailableException

router = APIRouter()

@router.post("/detect", response_model=DetectionResponse)
async def run_detection(
    request: DetectionRequest,
    m1: IMember1Adapter = Depends(get_m1)
):
    """Trigger Member 1 Cyclone Center Detection and Localization."""
    try:
        return await m1.detect(request)
    except MLServiceUnavailableException as e:
        raise HTTPException(status_code=503, detail=f"Member 1 Detection unavailable: {e.detail}")

@router.post("/classify", response_model=ClassificationResponse)
async def run_classification(
    request: ClassificationRequest,
    m1: IMember1Adapter = Depends(get_m1)
):
    """Trigger Member 1 Intensity Classification and Explainability map generation."""
    try:
        return await m1.classify(request)
    except MLServiceUnavailableException as e:
        raise HTTPException(status_code=503, detail=f"Member 1 Classification unavailable: {e.detail}")

@router.post("/predict")
async def run_composite_predict(
    request: DetectionRequest,
    m1: IMember1Adapter = Depends(get_m1)
) -> Dict[str, Any]:
    """Composite endpoint running Member 1 detection and classification."""
    try:
        det = await m1.detect(request)
        lat = det.latitude if det.latitude else 17.2
        lon = det.longitude if det.longitude else 87.3
        cls = await m1.classify(ClassificationRequest(image_id=request.image_id, latitude=lat, longitude=lon))
        return {
            "detected": det.detected,
            "latitude": det.latitude,
            "longitude": det.longitude,
            "confidence": det.confidence,
            "bbox": det.bbox,
            "classification": cls.classification,
            "estimated_wind_speed": cls.estimated_wind_speed,
            "model_version": f"{det.model_version}+{cls.model_version}"
        }
    except MLServiceUnavailableException as e:
        raise HTTPException(status_code=503, detail=f"Member 1 Predict unavailable: {e.detail}")

@router.post("/forecast", response_model=ForecastResponse)
async def run_forecast(
    request: ForecastRequest,
    m2: IMember2Adapter = Depends(get_m2)
):
    """Trigger Member 2 Multi-lead Trajectory and Intensity Forecasting."""
    try:
        return await m2.forecast(request)
    except MLServiceUnavailableException as e:
        raise HTTPException(status_code=503, detail=f"Member 2 Forecasting unavailable: {e.detail}")

@router.post("/track")
async def run_track_prediction(
    request: ForecastRequest,
    m2: IMember2Adapter = Depends(get_m2)
) -> Dict[str, Any]:
    """Trigger Member 2 Trajectory Prediction only."""
    try:
        fc = await m2.forecast(request)
        return {
            "cyclone_id": fc.cyclone_id,
            "forecast_time": fc.forecast_time,
            "model_version": fc.model_version,
            "track_points": [
                {
                    "lead_hours": pt.lead_hours,
                    "target_time": pt.target_time,
                    "latitude": pt.latitude,
                    "longitude": pt.longitude,
                    "uncertainty_radius_km": pt.uncertainty_radius_km,
                    "confidence": pt.confidence
                } for pt in fc.forecast_points
            ]
        }
    except MLServiceUnavailableException as e:
        raise HTTPException(status_code=503, detail=f"Member 2 Track unavailable: {e.detail}")

@router.post("/intensity")
async def run_intensity_prediction(
    request: ForecastRequest,
    m2: IMember2Adapter = Depends(get_m2)
) -> Dict[str, Any]:
    """Trigger Member 2 Intensity Prediction only."""
    try:
        fc = await m2.forecast(request)
        return {
            "cyclone_id": fc.cyclone_id,
            "forecast_time": fc.forecast_time,
            "model_version": fc.model_version,
            "intensity_points": [
                {
                    "lead_hours": pt.lead_hours,
                    "target_time": pt.target_time,
                    "predicted_wind_speed": pt.predicted_wind_speed,
                    "predicted_pressure": pt.predicted_pressure,
                    "confidence": pt.confidence
                } for pt in fc.forecast_points
            ]
        }
    except MLServiceUnavailableException as e:
        raise HTTPException(status_code=503, detail=f"Member 2 Intensity unavailable: {e.detail}")

@router.post("/full", response_model=UnifiedAnalysisResponse)
async def run_full_analysis(
    request: FullAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    m1: IMember1Adapter = Depends(get_m1),
    m2: IMember2Adapter = Depends(get_m2)
):
    """
    Execute end-to-end multi-member AI pipeline:
    1. Member 1 Detection (eye localization)
    2. Member 1 Classification (IMD category & Grad-CAM)
    3. Member 2 Trajectory & Intensity Prediction (+6h to +72h)
    4. PostGIS spatial persistence & unified JSON response
    """
    try:
        return await AnalysisOrchestrator.run_full_pipeline(
            db=db,
            request=request,
            member1=m1,
            member2=m2
        )
    except CycloneNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis pipeline execution failed: {str(e)}")
