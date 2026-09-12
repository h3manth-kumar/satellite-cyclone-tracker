"""
Domain and adapter specific exceptions.
"""

class CycloneAIException(Exception):
    """Base exception for CycloneAI platform."""
    pass

class CycloneNotFoundException(CycloneAIException):
    """Raised when a requested cyclone ID is not found."""
    pass

class SatelliteImageNotFoundException(CycloneAIException):
    """Raised when satellite image metadata or file is missing."""
    pass

class MLServiceUnavailableException(CycloneAIException):
    """Raised when peer ML detection or prediction microservice fails or times out."""
    def __init__(self, service_name: str, detail: str):
        self.service_name = service_name
        self.detail = detail
        super().__init__(f"{service_name} unavailable: {detail}")

class InsufficientObservationDataException(CycloneAIException):
    """Raised when insufficient historical observations exist to run forecasting models."""
    pass
