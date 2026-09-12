"""
Cyclone master model.
"""
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.base import Base

class Cyclone(Base):
    __tablename__ = "cyclones"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(100), nullable=True)
    basin = Column(String(50), nullable=False, index=True) # e.g. 'Bay of Bengal', 'Arabian Sea'
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    observations = relationship("Observation", back_populates="cyclone", cascade="all, delete-orphan", order_by="Observation.timestamp")
    forecasts = relationship("Forecast", back_populates="cyclone", cascade="all, delete-orphan", order_by="Forecast.target_time")
    satellite_images = relationship("SatelliteImage", back_populates="cyclone")
