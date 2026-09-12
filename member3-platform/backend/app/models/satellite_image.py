"""
Satellite image metadata model.
Large raster binaries are stored on disk, never in SQL.
"""
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.base import Base

class SatelliteImage(Base):
    __tablename__ = "satellite_images"

    id = Column(String(64), primary_key=True, index=True)
    cyclone_id = Column(String(64), ForeignKey("cyclones.id", ondelete="SET NULL"), nullable=True, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    satellite = Column(String(50), nullable=False) # e.g. 'INSAT-3D', 'INSAT-3DR'
    sensor = Column(String(50), nullable=False)    # e.g. 'IMAGER'
    channel = Column(String(30), nullable=False)   # e.g. 'TIR1', 'VIS', 'WV'
    file_path = Column(String(512), nullable=False)
    resolution_km = Column(Float, default=4.0)
    
    # Bounding box coordinates in decimal degrees WGS84
    min_lat = Column(Float, nullable=True)
    min_lon = Column(Float, nullable=True)
    max_lat = Column(Float, nullable=True)
    max_lon = Column(Float, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    cyclone = relationship("Cyclone", back_populates="satellite_images")
    detection_results = relationship("DetectionResult", back_populates="satellite_image", cascade="all, delete-orphan")
    classification_results = relationship("ClassificationResult", back_populates="satellite_image", cascade="all, delete-orphan")
