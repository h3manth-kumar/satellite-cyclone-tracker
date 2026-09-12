"""
CycloneAI Backend Application Entrypoint.
FastAPI REST API Gateway, PostGIS data hub, and ML pipeline orchestrator.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os

from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.core.exceptions import CycloneAIException
from app.db.session import init_tables, AsyncSessionLocal
from app.db.init_db import seed_initial_data
from app.api.v1.router import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION} [{settings.ENVIRONMENT}]")
    
    # Ensure local satellite data directories exist
    os.makedirs(os.path.join(settings.SATELLITE_DATA_DIR, "raw"), exist_ok=True)
    os.makedirs(os.path.join(settings.SATELLITE_DATA_DIR, "explainability"), exist_ok=True)
    
    # Initialize tables and seed initial records
    await init_tables()
    async with AsyncSessionLocal() as db:
        await seed_initial_data(db)
        
    yield
    # Shutdown
    logger.info("Shutting down CycloneAI platform backend.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Member 3 Application Platform for CycloneAI. "
        "Coordinates detection, classification, and forecasting across the North Indian Ocean."
    ),
    lifespan=lifespan
)

# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount main API router under /api/v1
app.include_router(api_router, prefix=settings.API_V1_STR)

# Also mount under root to satisfy top-level prompt contracts (/health, /cyclones, /analysis/...)
app.include_router(api_router)

@app.exception_handler(CycloneAIException)
async def cyclone_exception_handler(request: Request, exc: CycloneAIException):
    logger.error(f"Application exception on {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content={"error": exc.__class__.__name__, "detail": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.BACKEND_PORT, reload=True)
