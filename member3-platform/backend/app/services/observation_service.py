"""
Observation data access and management service.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.models.observation import Observation
from app.schemas.observation import ObservationCreate

class ObservationService:
    @staticmethod
    async def get_by_cyclone(
        db: AsyncSession,
        cyclone_id: str,
        limit: int = 100
    ) -> List[Observation]:
        query = select(Observation).where(
            Observation.cyclone_id == cyclone_id
        ).order_by(Observation.timestamp.asc()).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def create(
        db: AsyncSession,
        obs_in: ObservationCreate
    ) -> Observation:
        obs = Observation(
            cyclone_id=obs_in.cyclone_id,
            timestamp=obs_in.timestamp,
            latitude=obs_in.latitude,
            longitude=obs_in.longitude,
            wind_speed=obs_in.wind_speed,
            pressure=obs_in.pressure,
            classification=obs_in.classification,
            source=obs_in.source
        )
        db.add(obs)
        await db.commit()
        await db.refresh(obs)
        return obs
