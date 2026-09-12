"""FastAPI application factory and lifecycle management."""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router
from src.inference.engine import CycloneInferenceEngine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize ML model and engine
    weights_path = os.getenv("MODEL_WEIGHTS_PATH", "artifacts/models/cyclone_baseline_v1.pth")
    confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))
    device = os.getenv("DEVICE", "cpu")
    version = os.getenv("MODEL_VERSION", "v1.0.0")

    print(f"Initializing CycloneInferenceEngine [device={device}, version={version}]...")
    app.state.engine = CycloneInferenceEngine(
        weights_path=weights_path,
        device=device,
        confidence_threshold=confidence_threshold,
        version=version,
    )
    print("CycloneInferenceEngine successfully initialized.")

    yield

    # Shutdown: Clean up resources
    print("Shutting down ml-detection service...")


def create_app() -> FastAPI:
    app = FastAPI(
        title="CycloneAI - ML Detection & Classification Service",
        description="Subsystem for satellite image validation, cyclone detection, center localization, IMD stage classification, and Grad-CAM explainability.",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)
    return app


app = create_app()
