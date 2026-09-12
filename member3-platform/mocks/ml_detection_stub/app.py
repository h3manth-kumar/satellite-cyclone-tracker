"""
Member 1 ML Detection & Classification Service Stub
Provides reference contract endpoints for Member 1 integration.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
import datetime

app = FastAPI(
    title="CycloneAI - Member 1 Detection & Classification API",
    version="1.0.0",
    description="Microservice providing cyclone center detection, bounding box localization, and IMD intensity classification."
)

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    model_loaded: bool
    timestamp: str

class DetectionRequest(BaseModel):
    image_path: Optional[str] = None
    image_id: Optional[str] = None
    sensor: Optional[str] = "TIR1"

class DetectionResponse(BaseModel):
    detected: bool
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    confidence: float
    bbox: Optional[List[float]] = Field(default=None, description="[min_lat, min_lon, max_lat, max_lon]")
    model_version: str
    timestamp: str

class ClassificationRequest(BaseModel):
    image_path: Optional[str] = None
    image_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class ClassificationResponse(BaseModel):
    classification: str
    confidence: float
    estimated_wind_speed: float
    probabilities: Dict[str, float]
    model_version: str
    explainability_heatmap_path: Optional[str] = None
    timestamp: str

class PredictResponse(BaseModel):
    detected: bool
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    confidence: float
    bbox: Optional[List[float]] = None
    classification: str
    estimated_wind_speed: float
    model_version: str
    timestamp: str

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="ok",
        service="ml-detection",
        version="1.0.0",
        model_loaded=True,
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    )

@app.post("/detect", response_model=DetectionResponse)
async def detect_cyclone(req: DetectionRequest):
    return DetectionResponse(
        detected=True,
        latitude=17.25,
        longitude=87.35,
        confidence=0.942,
        bbox=[15.0, 85.0, 19.5, 89.7],
        model_version="m1-yolov8-v1.0.0",
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    )

@app.post("/classify", response_model=ClassificationResponse)
async def classify_cyclone(req: ClassificationRequest):
    return ClassificationResponse(
        classification="Very Severe Cyclonic Storm",
        confidence=0.884,
        estimated_wind_speed=76.5,
        probabilities={
            "Depression": 0.01,
            "Deep Depression": 0.02,
            "Cyclonic Storm": 0.04,
            "Severe Cyclonic Storm": 0.08,
            "Very Severe Cyclonic Storm": 0.78,
            "Extremely Severe Cyclonic Storm": 0.07
        },
        model_version="m1-resnet50-v1.0.0",
        explainability_heatmap_path="/app/data/satellite/explainability/exp_latest.png",
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    )

@app.post("/predict", response_model=PredictResponse)
async def predict_cyclone(req: DetectionRequest):
    return PredictResponse(
        detected=True,
        latitude=17.25,
        longitude=87.35,
        confidence=0.942,
        bbox=[15.0, 85.0, 19.5, 89.7],
        classification="Very Severe Cyclonic Storm",
        estimated_wind_speed=76.5,
        model_version="m1-composite-v1.0.0",
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8001, reload=False)
