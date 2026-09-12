"""
V1 API router bundling all endpoint routers.
"""
from fastapi import APIRouter
from app.api.v1.endpoints import health, cyclones, observations, satellite, analysis

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(cyclones.router, prefix="/cyclones", tags=["Cyclones"])
api_router.include_router(observations.router, prefix="/observations", tags=["Observations"])
api_router.include_router(satellite.router, prefix="/satellite", tags=["Satellite Imagery"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["AI Analysis Pipeline"])
