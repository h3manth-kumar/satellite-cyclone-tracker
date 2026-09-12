"""
Detection and Classification Result models representing Member 1 inference outputs.
"""
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone
from app.db.base import Base, GUID

class DetectionResult(Base):
    __tablename__ = "detection_results"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    image_id = Column(String(64), ForeignKey("satellite_images.id", ondelete="CASCADE"), nullable=False, index=True)
    detected = Column(Boolean, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    confidence = Column(Float, nullable=False)
    bbox_coordinates = Column(JSON, nullable=True) # [min_lat, min_lon, max_lat, max_lon]
    model_version = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    satellite_image = relationship("SatelliteImage", back_populates="detection_results")

class ClassificationResult(Base):
    __tablename__ = "classification_results"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    image_id = Column(String(64), ForeignKey("satellite_images.id", ondelete="CASCADE"), nullable=False, index=True)
    cyclone_id = Column(String(64), ForeignKey("cyclones.id", ondelete="SET NULL"), nullable=True, index=True)
    classification = Column(String(50), nullable=False) # IMD category
    confidence = Column(Float, nullable=False)
    estimated_wind_speed = Column(Float, nullable=True) # Knots
    class_probabilities = Column(JSON, nullable=True)
    explainability_file_path = Column(String(512), nullable=True)
    model_version = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    satellite_image = relationship("SatelliteImage", back_populates="classification_results")
