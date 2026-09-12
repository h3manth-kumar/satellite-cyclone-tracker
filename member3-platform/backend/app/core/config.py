"""
Application configuration management using Pydantic Settings.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "CycloneAI Decision Support Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # PostgreSQL / PostGIS Database URL
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://cyclone_admin:cyclone_secure_dev_password@postgres:5432/cyclone_db"
    )
    
    # ML Service Internal Docker Endpoints
    MEMBER1_URL: str = os.getenv("MEMBER1_URL", "http://ml-detection:8001")
    MEMBER2_URL: str = os.getenv("MEMBER2_URL", "http://ml-prediction:8002")
    
    # ML Adapter Controls
    USE_MOCK_ML: bool = os.getenv("USE_MOCK_ML", "true").lower() in ("true", "1", "yes")
    ML_TIMEOUT_SECONDS: float = float(os.getenv("ML_TIMEOUT_SECONDS", "15.0"))
    
    # File Storage for Satellite and Explainability Rasters
    SATELLITE_DATA_DIR: str = os.getenv("SATELLITE_DATA_DIR", "./data/satellite")
    
    # CORS Configuration
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://frontend:3000")

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="ignore"
    )

settings = Settings()
