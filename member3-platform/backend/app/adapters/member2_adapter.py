"""Concrete Member 2 service adapters: HTTP microservice client and resilient Mock."""

import time
import httpx
from datetime import datetime, timezone, timedelta
from typing import List

from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import MLServiceUnavailableException
from app.adapters.base import IMember2Adapter
from app.schemas.common import ServiceStatus
from app.schemas.member2 import ForecastRequest, ForecastResponse, ForecastPoint, ObservationStep


class HttpMember2Adapter(IMember2Adapter):
    """HTTP Client connecting to Member 2 microservice (ml-prediction:8002)."""

    def __init__(self, base_url: str = settings.MEMBER2_URL, timeout: float = settings.ML_TIMEOUT_SECONDS):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def check_health(self) -> ServiceStatus:
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{self.base_url}/health")
                latency_ms = round((time.time() - start_time) * 1000, 2)
                if resp.status_code == 200:
                    return ServiceStatus(status="online", url=self.base_url, latency_ms=latency_ms)
                else:
                    return ServiceStatus(status="degraded", url=self.base_url, latency_ms=latency_ms, error=f"HTTP {resp.status_code}")
        except Exception as exc:
            return ServiceStatus(status="offline", url=self.base_url, error=str(exc))

    async def forecast(self, request: ForecastRequest) -> ForecastResponse:
        obs_list = sorted(request.observations, key=lambda x: x.timestamp)
        if not obs_list:
            raise ValueError("Observation history cannot be empty.")

        # Member 2 requires at least 2 chronological observations for kinematic tracking
        if len(obs_list) == 1:
            first_obs = obs_list[0]
            try:
                dt = datetime.fromisoformat(first_obs.timestamp.replace("Z", "+00:00"))
            except Exception:
                dt = datetime.now(timezone.utc)
            prior_dt = dt - timedelta(hours=6)
            synth_obs = ObservationStep(
                timestamp=prior_dt.isoformat(),
                latitude=first_obs.latitude - 0.2,
                longitude=first_obs.longitude - 0.2,
                wind_speed=first_obs.wind_speed,
                pressure=first_obs.pressure,
            )
            obs_list = [synth_obs, first_obs]

        payload = {
            "cyclone_id": request.cyclone_id,
            "observations": [o.model_dump() for o in obs_list],
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(f"{self.base_url}/forecast", json=payload)
                if resp.status_code != 200:
                    raise MLServiceUnavailableException("Member 2 Prediction", f"HTTP {resp.status_code}: {resp.text}")
                data = resp.json()

                raw_preds = data.get("predictions", [])
                forecast_pts = []
                for p in raw_preds:
                    lead_h = p.get("hours", 6)
                    tgt_t = p.get("target_time")
                    if isinstance(tgt_t, datetime):
                        tgt_t = tgt_t.isoformat()
                    forecast_pts.append(
                        ForecastPoint(
                            lead_hours=lead_h,
                            target_time=str(tgt_t),
                            latitude=p.get("latitude"),
                            longitude=p.get("longitude"),
                            predicted_wind_speed=p.get("predicted_wind_speed"),
                            predicted_pressure=p.get("predicted_pressure"),
                            uncertainty_radius_km=p.get("error_radius_km", 50.0),
                            confidence=p.get("confidence", 0.8),
                        )
                    )

                model_version = data.get("model", {}).get("version", "track-model-v1.0")
                forecast_time = str(data.get("forecast_time", datetime.now(timezone.utc).isoformat()))

                return ForecastResponse(
                    cyclone_id=request.cyclone_id,
                    forecast_time=forecast_time,
                    model_version=model_version,
                    forecast_points=forecast_pts,
                )
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            logger.error(f"Member 2 Prediction unreachable at {self.base_url}: {exc}")
            raise MLServiceUnavailableException("Member 2 Prediction", str(exc))


class MockMember2Adapter(IMember2Adapter):
    """Resilient Mock Adapter delivering realistic trajectory predictions."""

    async def check_health(self) -> ServiceStatus:
        return ServiceStatus(status="online", url="mock://member2", latency_ms=3.1)

    async def forecast(self, request: ForecastRequest) -> ForecastResponse:
        obs_list = request.observations
        if not obs_list:
            raise ValueError("Observation history cannot be empty.")

        latest = obs_list[-1]
        try:
            base_time = datetime.fromisoformat(latest.timestamp.replace("Z", "+00:00"))
        except Exception:
            base_time = datetime.now(timezone.utc)

        base_wind = latest.wind_speed if latest.wind_speed is not None else 70.0
        base_pressure = latest.pressure if latest.pressure is not None else 975.0

        steps = [
            {"hours": 6, "dlat": 0.5, "dlon": 0.3, "dwind": 5.0, "dpres": -4.0, "radius": 25.0, "conf": 0.88},
            {"hours": 12, "dlat": 1.1, "dlon": 0.5, "dwind": 8.0, "dpres": -7.0, "radius": 45.0, "conf": 0.84},
            {"hours": 24, "dlat": 2.2, "dlon": 0.8, "dwind": 3.0, "dpres": -2.0, "radius": 75.0, "conf": 0.78},
            {"hours": 48, "dlat": 4.1, "dlon": 1.1, "dwind": -15.0, "dpres": 12.0, "radius": 130.0, "conf": 0.69},
        ]

        points = []
        for s in steps:
            target_t = base_time + timedelta(hours=s["hours"])
            pred_wind = max(20.0, min(160.0, round(base_wind + s["dwind"], 1)))
            pred_pres = max(890.0, min(1015.0, round(base_pressure + s["dpres"], 1)))

            points.append(
                ForecastPoint(
                    lead_hours=s["hours"],
                    target_time=target_t.isoformat(),
                    latitude=round(latest.latitude + s["dlat"], 3),
                    longitude=round(latest.longitude + s["dlon"], 3),
                    predicted_wind_speed=pred_wind,
                    predicted_pressure=pred_pres,
                    uncertainty_radius_km=s["radius"],
                    confidence=s["conf"],
                )
            )

        return ForecastResponse(
            cyclone_id=request.cyclone_id,
            forecast_time=datetime.now(timezone.utc).isoformat(),
            model_version="track-model-v1.0",
            forecast_points=points,
        )
