"""
FastAPI application entry point for CycloneAI ML Prediction service.
Service Name: ml-prediction
Port: 8002
"""

from pathlib import Path
import sys

# Ensure package root is in python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
import torch

from api.routes import router, set_inference_pipeline
from models.model_registry import load_model_pipeline, DEFAULT_MODEL_FILE

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("PredictionService")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup: load neural model, baseline, scaler, and uncertainty estimator.
    Shutdown: clean up GPU/CPU resources.
    """
    logger.info("Initializing ML Prediction Service...")
    device = "cuda" if torch.cuda.is_available() else "cpu"

    checkpoint_file = Path(__file__).resolve().parent.parent / "checkpoints" / "track_model_v1.pt"
    model, scaler, uncertainty_est, baseline = load_model_pipeline(
        checkpoint_path=checkpoint_file, device=device
    )

    set_inference_pipeline(model, scaler, uncertainty_est, baseline, device)
    logger.info(f"Model successfully initialized on device: {device}")

    yield

    logger.info("Shutting down ML Prediction Service...")


app = FastAPI(
    title="CycloneAI ML Prediction Service",
    description=(
        "Microservice for tropical cyclone track (lat/lon) and intensity (wind/pressure) "
        "forecasting with defensible uncertainty estimation for the North Indian Ocean."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for cross-container and local developer access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Formats validation errors cleanly into standard JSON.
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Request validation failed", "errors": exc.errors()},
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


# Mount routes
app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="0.0.0.0", port=8002, reload=False)
