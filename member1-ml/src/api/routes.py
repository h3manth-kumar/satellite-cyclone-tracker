"""API route endpoints for cyclone detection and classification service."""

import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse

from src.api.schemas import (
    HealthResponse,
    FullPredictionResponse,
    DetectionResult,
    ClassificationResult,
    ExplainabilityResult,
)
from src.preprocessing.image_loader import ImageValidationError

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service Health Check",
    tags=["Health"],
)
async def health_check(request: Request) -> HealthResponse:
    """Returns the operational status, device, and model loading state."""
    engine = request.app.state.engine
    return HealthResponse(
        status="healthy",
        service="ml-detection",
        version=engine.version,
        model_loaded=engine.weights_loaded or engine.model is not None,
        device=str(engine.device),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def _parse_bbox(bbox_str: Optional[str]) -> Optional[Dict[str, float]]:
    if not bbox_str:
        return None
    try:
        parsed = json.loads(bbox_str)
        if isinstance(parsed, dict) and all(k in parsed for k in ("min_lat", "max_lat", "min_lon", "max_lon")):
            return {k: float(parsed[k]) for k in ("min_lat", "max_lat", "min_lon", "max_lon")}
    except Exception:
        pass
    return None


@router.post(
    "/predict",
    response_model=FullPredictionResponse,
    summary="Complete Cyclone Analysis",
    tags=["Inference"],
)
async def predict_cyclone(
    request: Request,
    image: UploadFile = File(..., description="Satellite image file (PNG, JPEG, GeoTIFF, etc.)"),
    bbox: Optional[str] = Form(None, description='Optional JSON geo-bbox: {"min_lat": 10, "max_lat": 20, "min_lon": 80, "max_lon": 90}'),
    include_explainability: bool = Query(True, description="Whether to include Grad-CAM saliency map"),
    timestamp: Optional[str] = Form(None, description="Image timestamp in ISO-8601 format"),
) -> FullPredictionResponse:
    """
    Executes the full pipeline:
    - Preprocesses satellite image
    - Detects cyclone presence
    - Locates cyclone center
    - Classifies IMD intensity stage
    - Generates Grad-CAM visual explainability heatmap
    """
    engine = request.app.state.engine
    bbox_dict = _parse_bbox(bbox)

    try:
        image_bytes = await image.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="Uploaded image file is empty.")
        
        result = engine.analyze_image(
            image_input=image_bytes,
            bbox=bbox_dict,
            include_explainability=include_explainability,
            timestamp=timestamp,
        )
        return FullPredictionResponse(**result)

    except HTTPException:
        raise
    except ImageValidationError as e:
        raise HTTPException(status_code=422, detail=f"Image validation failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")


@router.post(
    "/detect",
    response_model=DetectionResult,
    summary="Fast-path Cyclone Detection",
    tags=["Inference"],
)
async def detect_only(
    request: Request,
    image: UploadFile = File(..., description="Satellite image file"),
    bbox: Optional[str] = Form(None, description="Optional JSON geo-bbox"),
) -> DetectionResult:
    """Performs rapid binary detection and center localization without full classification overhead."""
    engine = request.app.state.engine
    bbox_dict = _parse_bbox(bbox)

    try:
        image_bytes = await image.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="Uploaded image file is empty.")
        result = engine.analyze_image(
            image_input=image_bytes,
            bbox=bbox_dict,
            include_explainability=False,
        )
        return DetectionResult(**result["detection"])
    except HTTPException:
        raise
    except ImageValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/classify",
    response_model=ClassificationResult,
    summary="Cyclone Stage Classification",
    tags=["Inference"],
)
async def classify_only(
    request: Request,
    image: UploadFile = File(..., description="Satellite image file"),
) -> ClassificationResult:
    """Performs multi-class IMD cyclone intensity stage classification."""
    engine = request.app.state.engine

    try:
        image_bytes = await image.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="Uploaded image file is empty.")
        result = engine.analyze_image(
            image_input=image_bytes,
            include_explainability=False,
        )
        return ClassificationResult(**result["classification"])
    except HTTPException:
        raise
    except ImageValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/explain",
    response_model=ExplainabilityResult,
    summary="Grad-CAM Saliency Explanation",
    tags=["Explainability"],
)
async def explain_only(
    request: Request,
    image: UploadFile = File(..., description="Satellite image file"),
) -> ExplainabilityResult:
    """Generates Grad-CAM visual attention overlay."""
    engine = request.app.state.engine

    try:
        image_bytes = await image.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="Uploaded image file is empty.")
        result = engine.analyze_image(
            image_input=image_bytes,
            include_explainability=True,
        )
        return ExplainabilityResult(**result["explainability"])
    except HTTPException:
        raise
    except ImageValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
