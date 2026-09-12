"""
Observation model representing official and sensor ground truth.
Strictly separated from predictions.
"""
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone
from app.db.base import Base, GUID

class Observation(Base):
    __tablename__ = "observations"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    cyclone_id = Column(String(64), ForeignKey("cyclones.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    wind_speed = Column(Float, nullable=True) # Knots
    pressure = Column(Float, nullable=True)   # hPa
    classification = Column(String(50), nullable=True) # D, DD, CS, SCS, VSCS, ESCS, SuCS
    source = Column(String(50), nullable=False, default="IMD_OFFICIAL") # 'IMD_OFFICIAL', 'BUOY', 'SCAT'
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    cyclone = relationship("Cyclone", back_populates="observations")

    __table_args__ = (
        Index("idx_obs_cyclone_time", "cyclone_id", "timestamp"),
    )
