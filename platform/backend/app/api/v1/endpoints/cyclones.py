"""
Cyclone registry and spatial track API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.db.session import get_db
from app.services.cyclone_service import CycloneService
from app.services.observation_service import ObservationService
from app.schemas.cyclone import CycloneSummaryResponse, CycloneResponse
from app.schemas.observation import ObservationResponse
from app.schemas.common import GeoJSONFeatureCollection

router = APIRouter()

@router.get("", response_model=List[CycloneSummaryResponse])
async def list_cyclones(
    basin: Optional[str] = Query(None, description="Filter by ocean basin: 'Bay of Bengal', 'Arabian Sea'"),
    active_only: bool = Query(False, description="Return only currently active cyclones"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve list of monitored tropical cyclones with latest telemetry summary."""
    return await CycloneService.list_cyclones(db, basin=basin, active_only=active_only, limit=limit, offset=offset)

@router.get("/{cyclone_id}", response_model=CycloneResponse)
async def get_cyclone(
    cyclone_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve comprehensive details of a specific cyclone."""
    cyclone = await CycloneService.get_by_id(db, cyclone_id)
    if not cyclone:
        raise HTTPException(status_code=404, detail=f"Cyclone '{cyclone_id}' not found.")
    return cyclone

@router.get("/{cyclone_id}/observations", response_model=List[ObservationResponse])
async def get_cyclone_observations(
    cyclone_id: str,
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve historical ground-truth / sensor observations for a cyclone."""
    return await ObservationService.get_by_cyclone(db, cyclone_id, limit=limit)

@router.get("/{cyclone_id}/track-geojson", response_model=GeoJSONFeatureCollection)
async def get_cyclone_track_geojson(
    cyclone_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve RFC 7946 GeoJSON FeatureCollection containing observed track,
    forecast track, and uncertainty cones for direct Leaflet/MapLibre map rendering.
    """
    geojson = await CycloneService.get_track_geojson(db, cyclone_id)
    return geojson

@router.post("/{cyclone_id}/simulate-feed")
async def simulate_cyclone_feed(
    cyclone_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Simulate streaming live satellite/buoy telemetry into the cyclone track.
    Generates and persists the next synoptic observation waypoint.
    """
    res = await CycloneService.simulate_next_step(db, cyclone_id)
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res

@router.get("/{cyclone_id}/bulletin")
async def get_cyclone_bulletin(
    cyclone_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate an official IMD-standard Meteorological Cyclone Warning Advisory Bulletin.
    """
    res = await CycloneService.generate_bulletin(db, cyclone_id)
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res

