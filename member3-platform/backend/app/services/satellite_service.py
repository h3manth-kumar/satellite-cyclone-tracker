"""
Satellite imagery metadata and streaming service.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
import os
from app.models.satellite_image import SatelliteImage
from app.schemas.satellite import SatelliteImageResponse
from app.core.config import settings

class SatelliteService:
    @staticmethod
    async def list_images(
        db: AsyncSession,
        cyclone_id: Optional[str] = None,
        channel: Optional[str] = None,
        limit: int = 20
    ) -> List[SatelliteImageResponse]:
        query = select(SatelliteImage).order_by(desc(SatelliteImage.timestamp))
        if cyclone_id:
            query = query.where(SatelliteImage.cyclone_id == cyclone_id)
        if channel:
            query = query.where(SatelliteImage.channel == channel)
        
        query = query.limit(limit)
        result = await db.execute(query)
        images = result.scalars().all()

        responses = []
        for img in images:
            responses.append(SatelliteImageResponse(
                id=img.id,
                cyclone_id=img.cyclone_id,
                timestamp=img.timestamp,
                satellite=img.satellite,
                sensor=img.sensor,
                channel=img.channel,
                file_path=img.file_path,
                resolution_km=img.resolution_km,
                min_lat=img.min_lat,
                min_lon=img.min_lon,
                max_lat=img.max_lat,
                max_lon=img.max_lon,
                created_at=img.created_at,
                download_url=f"/api/v1/satellite/images/{img.id}/file"
            ))
        return responses

    @staticmethod
    async def get_by_id(db: AsyncSession, image_id: str) -> Optional[SatelliteImage]:
        query = select(SatelliteImage).where(SatelliteImage.id == image_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    def resolve_image_file_path(image_filename: str) -> str:
        """Resolve full filesystem path to satellite raster."""
        clean_name = os.path.basename(image_filename)
        return os.path.join(settings.SATELLITE_DATA_DIR, "raw", clean_name)

    @staticmethod
    def resolve_explainability_file_path(filename: str) -> str:
        """Resolve full filesystem path to Grad-CAM heatmap."""
        clean_name = os.path.basename(filename)
        return os.path.join(settings.SATELLITE_DATA_DIR, "explainability", clean_name)
