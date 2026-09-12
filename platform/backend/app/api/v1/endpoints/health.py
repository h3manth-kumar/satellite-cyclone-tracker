"""
System and microservices health check endpoint.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime, timezone
import time
from app.db.session import get_db
from app.adapters.base import IMember1Adapter, IMember2Adapter
from app.api.deps import get_m1, get_m2
from app.schemas.common import HealthResponse, ServiceStatus
from app.core.config import settings

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def get_system_health(
    db: AsyncSession = Depends(get_db),
    m1: IMember1Adapter = Depends(get_m1),
    m2: IMember2Adapter = Depends(get_m2),
):
    # 1. Test Database
    db_status = {"status": "connected"}
    try:
        t0 = time.time()
        await db.execute(text("SELECT 1"))
        db_status["latency_ms"] = round((time.time() - t0) * 1000, 2)
    except Exception as e:
        db_status = {"status": "disconnected", "error": str(e)}

    # 2. Test Member 1 and Member 2 Service Health
    m1_status = await m1.check_health()
    m2_status = await m2.check_health()

    overall_status = "healthy"
    if db_status.get("status") != "connected":
        overall_status = "unhealthy"
    elif m1_status.status == "offline" or m2_status.status == "offline":
        overall_status = "degraded"

    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now(timezone.utc),
        version=settings.VERSION,
        database=db_status,
        services={
            "ml_detection": m1_status,
            "ml_prediction": m2_status,
        }
    )
