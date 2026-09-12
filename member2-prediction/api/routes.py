"""
FastAPI route handlers for ML Prediction service.
"""

from datetime import timedelta
import logging
from typing import Dict, Any, List, Tuple
from fastapi import APIRouter, HTTPException, status
import numpy as np
import torch

from api.schemas import (
    ForecastRequest,
    ForecastResponse,
    TrackResponse,
    TrackPredictionItem,
    IntensityResponse,
    IntensityPredictionItem,
    SingleHorizonPrediction,
    HealthResponse,
    ModelInfo,
)
from data.features import extract_features_from_sequence
from data.dataset import HORIZON_HOURS

logger = logging.getLogger("ApiRoutes")
router = APIRouter()

# Globals initialized in lifespan in main.py
MODEL = None
SCALER = None
UNCERTAINTY_EST = None
BASELINE = None
DEVICE = "cpu"


def set_inference_pipeline(model, scaler, uncertainty_est, baseline, device):
    global MODEL, SCALER, UNCERTAINTY_EST, BASELINE, DEVICE
    MODEL = model
    SCALER = scaler
    UNCERTAINTY_EST = uncertainty_est
    BASELINE = baseline
    DEVICE = device


def _prepare_model_input(observations: List[Any]) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Transforms raw API observations into model tensor and current state.
    Pads if observations length is between 2 and 3.
    """
    obs_dicts = [o.model_dump() for o in observations]
    raw_feats = extract_features_from_sequence(obs_dicts)  # [N, 12]

    # If shorter than lookback (4), repeat first observation to pad
    lookback = 4
    if len(raw_feats) < lookback:
        pad_count = lookback - len(raw_feats)
        padding = np.repeat(raw_feats[:1], pad_count, axis=0)
        raw_feats = np.vstack([padding, raw_feats])
    elif len(raw_feats) > lookback:
        raw_feats = raw_feats[-lookback:]

    # Scale features
    if SCALER is not None:
        scaled_feats = SCALER.transform(raw_feats)
    else:
        scaled_feats = raw_feats

    x_tensor = torch.tensor(scaled_feats, dtype=torch.float32).unsqueeze(0).to(DEVICE)

    # Current state: lat, lon, wind, pres from last observation
    last_obs = observations[-1]
    curr_lat = float(last_obs.latitude)
    curr_lon = float(last_obs.longitude)
    curr_wind = float(last_obs.wind_speed or 0.0)
    curr_pres = float(last_obs.pressure or 1000.0)

    curr_state_tensor = torch.tensor(
        [[curr_lat, curr_lon, curr_wind, curr_pres]], dtype=torch.float32
    ).to(DEVICE)

    return x_tensor, curr_state_tensor


@router.get("/health", response_model=HealthResponse, tags=["Diagnostics"])
def health_check():
    """
    Healthcheck endpoint reporting service status, version, and device.
    """
    version = getattr(MODEL, "version", "track-model-v1.0") if MODEL else "uninitialized"
    return HealthResponse(
        status="ok",
        service="ml-prediction",
        model_version=version,
        device=str(DEVICE),
    )


@router.post("/forecast", response_model=ForecastResponse, tags=["Forecasting"])
def generate_forecast(req: ForecastRequest):
    """
    Generates joint track (lat/lon) and intensity (wind/pressure) forecast
    with 95% uncertainty cones and calibrated confidence scores.
    """
    if len(req.observations) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 2 chronological observations required for motion tracking.",
        )

    last_obs = req.observations[-1]
    forecast_origin_time = last_obs.timestamp

    try:
        x_tensor, curr_state_tensor = _prepare_model_input(req.observations)

        # Run uncertainty estimation via Monte Carlo Dropout
        unc_results = UNCERTAINTY_EST.estimate(MODEL, x_tensor, curr_state_tensor)

        mean_track = unc_results["mean_track"][0]  # [4, 2]
        mean_intensity = unc_results["mean_intensity"][0]  # [4, 2]
        error_radius = unc_results["error_radius_km"][0]  # [4]
        confidence = unc_results["confidence"][0]  # [4]

        predictions = []
        for idx, hours in enumerate(HORIZON_HOURS):
            target_time = forecast_origin_time + timedelta(hours=hours)

            lat = float(mean_track[idx, 0])
            lon = float(mean_track[idx, 1])
            wind = float(mean_intensity[idx, 0])
            pres = float(mean_intensity[idx, 1])

            # Only output intensity predictions if input observations provided valid intensity data
            has_input_wind = last_obs.wind_speed is not None
            has_input_pres = last_obs.pressure is not None

            pred_wind_val = round(wind, 1) if (has_input_wind and wind > 0) else None
            pred_pres_val = round(pres, 1) if (has_input_pres and 800 < pres < 1050) else None

            predictions.append(
                SingleHorizonPrediction(
                    hours=hours,
                    target_time=target_time,
                    latitude=round(lat, 3),
                    longitude=round(lon, 3),
                    predicted_wind_speed=pred_wind_val,
                    predicted_pressure=pred_pres_val,
                    confidence=round(float(confidence[idx]), 3),
                    error_radius_km=round(float(error_radius[idx]), 1),
                )
            )

        return ForecastResponse(
            cyclone_id=req.cyclone_id,
            forecast_time=forecast_origin_time,
            predictions=predictions,
            model=ModelInfo(name="CycloneTrackGRU", version=getattr(MODEL, "version", "track-model-v1.0")),
        )

    except Exception as e:
        logger.error(f"Inference error in /forecast: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/track", response_model=TrackResponse, tags=["Forecasting"])
def predict_track(req: ForecastRequest):
    """
    Dedicated track prediction endpoint returning projected coordinates, error radius, and confidence.
    """
    full_forecast = generate_forecast(req)
    track_items = [
        TrackPredictionItem(
            hours=p.hours,
            target_time=p.target_time,
            latitude=p.latitude,
            longitude=p.longitude,
            confidence=p.confidence,
            error_radius_km=p.error_radius_km,
        )
        for p in full_forecast.predictions
    ]
    return TrackResponse(
        cyclone_id=full_forecast.cyclone_id,
        forecast_time=full_forecast.forecast_time,
        predictions=track_items,
        model=full_forecast.model,
    )


@router.post("/intensity", response_model=IntensityResponse, tags=["Forecasting"])
def predict_intensity(req: ForecastRequest):
    """
    Dedicated intensity prediction endpoint returning projected wind speed and central pressure.
    """
    full_forecast = generate_forecast(req)
    intensity_items = [
        IntensityPredictionItem(
            hours=p.hours,
            target_time=p.target_time,
            predicted_wind_speed=p.predicted_wind_speed,
            predicted_pressure=p.predicted_pressure,
            confidence=p.confidence,
        )
        for p in full_forecast.predictions
    ]
    return IntensityResponse(
        cyclone_id=full_forecast.cyclone_id,
        forecast_time=full_forecast.forecast_time,
        predictions=intensity_items,
        model=full_forecast.model,
    )
