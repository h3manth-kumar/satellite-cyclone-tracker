"""
Full Analysis Pipeline Orchestrator.
Coordinates Member 1 (Detection & Classification) and Member 2 (Forecasting),
enforces data provenance, persists results, and compiles unified response.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from app.models.cyclone import Cyclone
from app.models.observation import Observation
from app.models.satellite_image import SatelliteImage
from app.models.detection_result import DetectionResult, ClassificationResult
from app.models.forecast import Forecast
from app.adapters.base import IMember1Adapter, IMember2Adapter
from app.schemas.analysis import FullAnalysisRequest, UnifiedAnalysisResponse
from app.schemas.member1 import (
    DetectionRequest, DetectionResponse,
    ClassificationRequest, ClassificationResponse
)
from app.schemas.member2 import ForecastRequest, ForecastResponse, ObservationStep, ForecastPoint
from app.core.exceptions import (
    CycloneNotFoundException, MLServiceUnavailableException
)
from app.core.logging import logger

class AnalysisOrchestrator:
    @staticmethod
    async def run_full_pipeline(
        db: AsyncSession,
        request: FullAnalysisRequest,
        member1: IMember1Adapter,
        member2: IMember2Adapter
    ) -> UnifiedAnalysisResponse:
        warnings: List[str] = []
        models_used: Dict[str, str] = {}
        status = "success"

        # 1. Fetch Cyclone master record
        cyclone_query = await db.execute(select(Cyclone).where(Cyclone.id == request.cyclone_id))
        cyclone = cyclone_query.scalar_one_or_none()
        if not cyclone:
            raise CycloneNotFoundException(f"Cyclone with ID '{request.cyclone_id}' not found.")
        
        cyclone_info = {
            "id": cyclone.id,
            "name": cyclone.name,
            "basin": cyclone.basin,
            "is_active": cyclone.is_active
        }

        # 2. Fetch Latest Observation for Ground-Truth Context
        obs_query = await db.execute(
            select(Observation)
            .where(Observation.cyclone_id == cyclone.id)
            .order_by(desc(Observation.timestamp))
            .limit(1)
        )
        latest_obs = obs_query.scalar_one_or_none()
        obs_data = None
        if latest_obs:
            obs_data = {
                "timestamp": latest_obs.timestamp.isoformat(),
                "latitude": latest_obs.latitude,
                "longitude": latest_obs.longitude,
                "wind_speed": latest_obs.wind_speed,
                "pressure": latest_obs.pressure,
                "classification": latest_obs.classification,
                "source": latest_obs.source,
                "provenance": "GROUND_TRUTH_OBSERVED"
            }

        # 3. Resolve Satellite Image Metadata
        image_obj = None
        if request.satellite_image_id:
            img_query = await db.execute(select(SatelliteImage).where(SatelliteImage.id == request.satellite_image_id))
            image_obj = img_query.scalar_one_or_none()
        else:
            # Pick latest image for this cyclone
            img_query = await db.execute(
                select(SatelliteImage)
                .where(SatelliteImage.cyclone_id == cyclone.id)
                .order_by(desc(SatelliteImage.timestamp))
                .limit(1)
            )
            image_obj = img_query.scalar_one_or_none()

        # 4. Member 1: Cyclone Center Detection
        detection_res: Optional[DetectionResponse] = None
        try:
            det_req = DetectionRequest(
                image_id=image_obj.id if image_obj else None,
                image_path=image_obj.file_path if image_obj else None,
                sensor=image_obj.sensor if image_obj else "TIR1"
            )
            detection_res = await member1.detect(det_req)
            models_used["detection"] = detection_res.model_version

            if request.persist_results and image_obj and detection_res:
                det_record = DetectionResult(
                    image_id=image_obj.id,
                    detected=detection_res.detected,
                    latitude=detection_res.latitude,
                    longitude=detection_res.longitude,
                    confidence=detection_res.confidence,
                    bbox_coordinates=detection_res.bbox,
                    model_version=detection_res.model_version
                )
                db.add(det_record)
        except MLServiceUnavailableException as e:
            logger.warning(f"Member 1 Detection unavailable: {e.detail}")
            warnings.append("ML Detection Service is currently offline or degraded.")
            status = "partial_success"
        except Exception as e:
            logger.error(f"Unexpected detection error: {e}")
            warnings.append(f"Detection error: {str(e)}")
            status = "partial_success"

        # 5. Member 1: IMD Intensity Classification
        classification_res: Optional[ClassificationResponse] = None
        center_lat = detection_res.latitude if (detection_res and detection_res.latitude) else (latest_obs.latitude if latest_obs else 15.0)
        center_lon = detection_res.longitude if (detection_res and detection_res.longitude) else (latest_obs.longitude if latest_obs else 85.0)

        try:
            cls_req = ClassificationRequest(
                image_id=image_obj.id if image_obj else None,
                image_path=image_obj.file_path if image_obj else None,
                latitude=center_lat,
                longitude=center_lon
            )
            classification_res = await member1.classify(cls_req)
            models_used["classification"] = classification_res.model_version

            if request.persist_results and image_obj and classification_res:
                cls_record = ClassificationResult(
                    image_id=image_obj.id,
                    cyclone_id=cyclone.id,
                    classification=classification_res.classification,
                    confidence=classification_res.confidence,
                    estimated_wind_speed=classification_res.estimated_wind_speed,
                    class_probabilities=classification_res.probabilities,
                    explainability_file_path=classification_res.explainability_heatmap_path,
                    model_version=classification_res.model_version
                )
                db.add(cls_record)
        except MLServiceUnavailableException as e:
            logger.warning(f"Member 1 Classification unavailable: {e.detail}")
            warnings.append("ML Classification Service is currently offline or degraded.")
            status = "partial_success"
        except Exception as e:
            logger.error(f"Unexpected classification error: {e}")
            warnings.append(f"Classification error: {str(e)}")
            status = "partial_success"

        # 6. Member 2: Trajectory & Intensity Forecasting
        forecast_points: List[ForecastPoint] = []
        try:
            # Query past observation sequence (at least last 4-6 points)
            obs_history_query = await db.execute(
                select(Observation)
                .where(Observation.cyclone_id == cyclone.id)
                .order_by(Observation.timestamp.asc())
            )
            obs_history = list(obs_history_query.scalars().all())

            history_steps = []
            for obs in obs_history:
                history_steps.append(ObservationStep(
                    timestamp=obs.timestamp.isoformat(),
                    latitude=obs.latitude,
                    longitude=obs.longitude,
                    wind_speed=obs.wind_speed,
                    pressure=obs.pressure
                ))

            # If no history exists, synthesize from current detection/observation point
            if not history_steps:
                history_steps = [ObservationStep(
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    latitude=center_lat,
                    longitude=center_lon,
                    wind_speed=classification_res.estimated_wind_speed if classification_res else 65.0,
                    pressure=980.0
                )]

            fc_req = ForecastRequest(
                cyclone_id=cyclone.id,
                observations=history_steps
            )
            fc_res: ForecastResponse = await member2.forecast(fc_req)
            models_used["prediction"] = fc_res.model_version
            forecast_points = fc_res.forecast_points

            if request.persist_results and forecast_points:
                now_utc = datetime.now(timezone.utc)
                # Clear previous forecasts for this cyclone to keep active forecast clean
                # or insert new run
                for pt in forecast_points:
                    target_dt = datetime.fromisoformat(pt.target_time.replace("Z", "+00:00"))
                    fc_record = Forecast(
                        cyclone_id=cyclone.id,
                        forecast_time=now_utc,
                        target_time=target_dt,
                        lead_hours=pt.lead_hours,
                        latitude=pt.latitude,
                        longitude=pt.longitude,
                        predicted_wind_speed=pt.predicted_wind_speed,
                        predicted_pressure=pt.predicted_pressure,
                        uncertainty_radius_km=pt.uncertainty_radius_km,
                        confidence=pt.confidence,
                        model_version=fc_res.model_version
                    )
                    db.add(fc_record)
        except MLServiceUnavailableException as e:
            logger.warning(f"Member 2 Prediction unavailable: {e.detail}")
            warnings.append("ML Forecasting Service is currently offline or degraded. No forecast generated.")
            status = "partial_success"
        except Exception as e:
            logger.error(f"Unexpected forecast error: {e}")
            warnings.append(f"Forecasting error: {str(e)}")
            status = "partial_success"

        # Commit all persisted records if requested
        if request.persist_results:
            try:
                await db.commit()
            except Exception as commit_err:
                logger.error(f"Error persisting analysis results: {commit_err}")
                await db.rollback()

        if len(warnings) >= 3:
            status = "failed"

        return UnifiedAnalysisResponse(
            timestamp=datetime.now(timezone.utc).isoformat(),
            status=status,
            cyclone=cyclone_info,
            observation=obs_data,
            detection=detection_res,
            classification=classification_res,
            forecast=forecast_points,
            models=models_used,
            warnings=warnings
        )
