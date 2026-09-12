"""
Member 2 ML Track & Intensity Forecasting Service Stub
Provides reference contract endpoints for Member 2 integration.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
import datetime

app = FastAPI(
    title="CycloneAI - Member 2 Trajectory & Intensity Prediction API",
    version="1.0.0",
    description="Microservice providing multi-lead time cyclone track and intensity forecasts."
)

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    model_loaded: bool
    timestamp: str

class ObservationStep(BaseModel):
    timestamp: str
    latitude: float
    longitude: float
    wind_speed: Optional[float] = None
    pressure: Optional[float] = None

class ForecastRequest(BaseModel):
    cyclone_id: str
    history: List[ObservationStep] = Field(..., min_length=1, description="Sequence of past observations (at least 1 point required)")

class ForecastPoint(BaseModel):
    lead_hours: int
    target_time: str
    latitude: float
    longitude: float
    predicted_wind_speed: float
    predicted_pressure: float
    uncertainty_radius_km: float
    confidence: float

class ForecastResponse(BaseModel):
    cyclone_id: str
    forecast_time: str
    model_version: str
    forecast_points: List[ForecastPoint]

class TrackPoint(BaseModel):
    lead_hours: int
    target_time: str
    latitude: float
    longitude: float
    uncertainty_radius_km: float
    confidence: float

class TrackResponse(BaseModel):
    cyclone_id: str
    forecast_time: str
    model_version: str
    track_points: List[TrackPoint]

class IntensityPoint(BaseModel):
    lead_hours: int
    target_time: str
    predicted_wind_speed: float
    predicted_pressure: float
    confidence: float

class IntensityResponse(BaseModel):
    cyclone_id: str
    forecast_time: str
    model_version: str
    intensity_points: List[IntensityPoint]

def _compute_forecast_points(req: ForecastRequest) -> List[ForecastPoint]:
    latest = req.history[-1]
    try:
        base_time = datetime.datetime.fromisoformat(latest.timestamp.replace("Z", "+00:00"))
    except Exception:
        base_time = datetime.datetime.now(datetime.timezone.utc)

    lead_steps = [
        {"hours": 6, "dlat": 0.5, "dlon": 0.3, "dwind": 5.0, "dpres": -4.0, "radius": 25.0, "conf": 0.88},
        {"hours": 12, "dlat": 1.1, "dlon": 0.5, "dwind": 8.0, "dpres": -7.0, "radius": 45.0, "conf": 0.84},
        {"hours": 24, "dlat": 2.2, "dlon": 0.8, "dwind": 3.0, "dpres": -2.0, "radius": 75.0, "conf": 0.78},
        {"hours": 48, "dlat": 4.1, "dlon": 1.1, "dwind": -15.0, "dpres": 12.0, "radius": 130.0, "conf": 0.69},
        {"hours": 72, "dlat": 5.6, "dlon": 1.2, "dwind": -35.0, "dpres": 30.0, "radius": 190.0, "conf": 0.58},
    ]

    base_wind = latest.wind_speed if latest.wind_speed is not None else 65.0
    base_pressure = latest.pressure if latest.pressure is not None else 980.0

    points = []
    for step in lead_steps:
        target_t = base_time + datetime.timedelta(hours=step["hours"])
        pred_wind = max(20.0, min(160.0, round(base_wind + step["dwind"], 1)))
        pred_pres = max(890.0, min(1015.0, round(base_pressure + step["dpres"], 1)))

        points.append(ForecastPoint(
            lead_hours=step["hours"],
            target_time=target_t.isoformat(),
            latitude=round(latest.latitude + step["dlat"], 3),
            longitude=round(latest.longitude + step["dlon"], 3),
            predicted_wind_speed=pred_wind,
            predicted_pressure=pred_pres,
            uncertainty_radius_km=step["radius"],
            confidence=step["conf"]
        ))
    return points

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="ok",
        service="ml-prediction",
        version="1.0.0",
        model_loaded=True,
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    )

@app.post("/forecast", response_model=ForecastResponse)
async def generate_forecast(req: ForecastRequest):
    if not req.history:
        raise HTTPException(status_code=422, detail="At least 1 historical observation step is required.")
    pts = _compute_forecast_points(req)
    return ForecastResponse(
        cyclone_id=req.cyclone_id,
        forecast_time=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        model_version="m2-tft-transformer-v1.0.0",
        forecast_points=pts
    )

@app.post("/track", response_model=TrackResponse)
async def generate_track(req: ForecastRequest):
    if not req.history:
        raise HTTPException(status_code=422, detail="At least 1 historical observation step is required.")
    pts = _compute_forecast_points(req)
    track_pts = [
        TrackPoint(
            lead_hours=p.lead_hours,
            target_time=p.target_time,
            latitude=p.latitude,
            longitude=p.longitude,
            uncertainty_radius_km=p.uncertainty_radius_km,
            confidence=p.confidence
        ) for p in pts
    ]
    return TrackResponse(
        cyclone_id=req.cyclone_id,
        forecast_time=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        model_version="m2-tft-transformer-v1.0.0",
        track_points=track_pts
    )

@app.post("/intensity", response_model=IntensityResponse)
async def generate_intensity(req: ForecastRequest):
    if not req.history:
        raise HTTPException(status_code=422, detail="At least 1 historical observation step is required.")
    pts = _compute_forecast_points(req)
    intensity_pts = [
        IntensityPoint(
            lead_hours=p.lead_hours,
            target_time=p.target_time,
            predicted_wind_speed=p.predicted_wind_speed,
            predicted_pressure=p.predicted_pressure,
            confidence=p.confidence
        ) for p in pts
    ]
    return IntensityResponse(
        cyclone_id=req.cyclone_id,
        forecast_time=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        model_version="m2-tft-transformer-v1.0.0",
        intensity_points=intensity_pts
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8002, reload=False)
