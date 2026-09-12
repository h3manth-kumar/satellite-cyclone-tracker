"""
Forecast and Model Registry models.
Forecasts represent Member 2 predictions and are strictly isolated from observations.
"""
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Index, JSON, Boolean
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone
from app.db.base import Base, GUID

class Forecast(Base):
    __tablename__ = "forecasts"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    cyclone_id = Column(String(64), ForeignKey("cyclones.id", ondelete="CASCADE"), nullable=False, index=True)
    forecast_time = Column(DateTime(timezone=True), nullable=False) # When model ran
    target_time = Column(DateTime(timezone=True), nullable=False, index=True) # Valid at
    lead_hours = Column(Integer, nullable=False) # +6, +12, +24, +48, +72
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    predicted_wind_speed = Column(Float, nullable=True) # Knots
    predicted_pressure = Column(Float, nullable=True)   # hPa
    uncertainty_radius_km = Column(Float, default=30.0) # Error cone radius
    confidence = Column(Float, nullable=False)
    model_version = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    cyclone = relationship("Cyclone", back_populates="forecasts")

    __table_args__ = (
        Index("idx_forecast_cyclone_target", "cyclone_id", "target_time"),
    )

class ModelRegistry(Base):
    __tablename__ = "models"

    id = Column(String(64), primary_key=True, index=True)
    service_name = Column(String(50), nullable=False) # 'ml-detection', 'ml-prediction'
    version = Column(String(50), nullable=False)
    description = Column(String(255), nullable=True)
    metrics = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
