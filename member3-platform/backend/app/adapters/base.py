"""
Abstract interfaces for Member 1 and Member 2 ML service adapters.
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from app.schemas.member1 import (
    DetectionRequest, DetectionResponse,
    ClassificationRequest, ClassificationResponse
)
from app.schemas.member2 import ForecastRequest, ForecastResponse
from app.schemas.common import ServiceStatus

class IMember1Adapter(ABC):
    """Adapter interface for Member 1 Detection and Classification subsystem."""

    @abstractmethod
    async def check_health(self) -> ServiceStatus:
        """Query reachability and health of Member 1 service."""
        pass

    @abstractmethod
    async def detect(self, request: DetectionRequest) -> DetectionResponse:
        """Detect cyclone presence, bounding box, and center coordinate."""
        pass

    @abstractmethod
    async def classify(self, request: ClassificationRequest) -> ClassificationResponse:
        """Classify intensity into IMD category and return estimated sustained winds."""
        pass

class IMember2Adapter(ABC):
    """Adapter interface for Member 2 Trajectory and Intensity Forecasting subsystem."""

    @abstractmethod
    async def check_health(self) -> ServiceStatus:
        """Query reachability and health of Member 2 service."""
        pass

    @abstractmethod
    async def forecast(self, request: ForecastRequest) -> ForecastResponse:
        """Generate multi-step trajectory and intensity predictions."""
        pass
