"""
Ground-truth / sensor observations ingestion endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.observation import ObservationCreate, ObservationResponse
from app.services.observation_service import ObservationService

router = APIRouter()

@router.post("", response_model=ObservationResponse, status_code=201)
async def create_observation(
    obs_in: ObservationCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Ingest a verified meteorological ground-truth observation (e.g. from IMD best tracks, buoys, or scatterometer).
    Never use this endpoint to store AI model predictions.
    """
    return await ObservationService.create(db, obs_in)
