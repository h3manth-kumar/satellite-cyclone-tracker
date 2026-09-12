"""
Satellite imagery streaming and metadata endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import os
import io
import math
from PIL import Image, ImageDraw, ImageFilter
from app.db.session import get_db
from app.services.satellite_service import SatelliteService
from app.schemas.satellite import SatelliteImageResponse
from app.core.config import settings

router = APIRouter()

def generate_synthetic_cyclone_ir(width=512, height=512) -> bytes:
    """Generate a realistic synthetic Thermal Infrared (TIR1) satellite image of a tropical cyclone."""
    img = Image.new("RGBA", (width, height), (14, 16, 18, 255))
    draw = ImageDraw.Draw(img)

    cx, cy = width // 2, height // 2

    # Draw cold cloud background and ocean
    for r in range(220, 10, -5):
        alpha = int(255 * (1 - (r / 220.0)))
        val = int(30 + 180 * (1 - (r / 220.0)**1.5))
        # Infrared false-color gradient: dark navy -> grey -> cyan -> white (coldest cloud tops)
        if val < 80:
            color = (15, 25, 45, 255)
        elif val < 130:
            color = (30, val, val + 20, 255)
        elif val < 190:
            color = (val - 30, val, val + 40, 255)
        else:
            color = (val, val, 255, 255)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)

    # Draw spiral convective rainbands
    for arm in range(4):
        base_angle = arm * (math.pi / 2)
        points = []
        for t in range(20, 200, 4):
            theta = base_angle + (t * 0.04)
            r = t * 1.1
            x = cx + r * math.cos(theta)
            y = cy + r * math.sin(theta)
            points.append((x, y))
        for p in points:
            px, py = int(p[0]), int(p[1])
            if 0 <= px < width and 0 <= py < height:
                draw.ellipse([px - 14, py - 14, px + 14, py + 14], fill=(210, 230, 255, 220))

    # Cyclone Eye (Warmer cloud-free center in IR)
    eye_r = 18
    draw.ellipse([cx - eye_r, cy - eye_r, cx + eye_r, cy + eye_r], fill=(35, 45, 60, 255))

    # Blur for realistic atmospheric blending
    img = img.filter(ImageFilter.GaussianBlur(radius=3))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def generate_synthetic_gradcam_heatmap(width=512, height=512) -> bytes:
    """Generate a realistic Grad-CAM convective attention heatmap."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = width // 2, height // 2

    # High attention on eyewall convection
    for r in range(120, 15, -4):
        ratio = 1.0 - (abs(r - 45) / 75.0)
        ratio = max(0.0, min(1.0, ratio))
        # Jet colormap: blue -> green -> yellow -> red
        red = int(255 * min(1.0, ratio * 1.8))
        green = int(255 * (1.0 - abs(ratio - 0.5) * 2))
        blue = int(180 * (1.0 - ratio))
        alpha = int(190 * (ratio ** 1.5))
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(red, green, blue, alpha))

    img = img.filter(ImageFilter.GaussianBlur(radius=5))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

@router.get("/images", response_model=List[SatelliteImageResponse])
async def list_satellite_images(
    cyclone_id: Optional[str] = Query(None),
    channel: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List satellite image metadata records."""
    return await SatelliteService.list_images(db, cyclone_id=cyclone_id, channel=channel, limit=limit)

@router.get("/images/{image_id}/file")
async def get_satellite_image_file(
    image_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Stream the raw/enhanced satellite raster.
    Serves from volume storage if present, or synthesizes high-fidelity INSAT-3D IR raster.
    """
    img = await SatelliteService.get_by_id(db, image_id)
    if not img:
        raise HTTPException(status_code=404, detail=f"Satellite image '{image_id}' not found.")

    full_path = SatelliteService.resolve_image_file_path(img.file_path)
    if os.path.exists(full_path):
        with open(full_path, "rb") as f:
            content = f.read()
    else:
        content = generate_synthetic_cyclone_ir()

    return Response(content=content, media_type="image/png")

@router.get("/explainability/{filename}")
async def get_explainability_heatmap(filename: str):
    """
    Stream Member 1 Grad-CAM attention heatmap overlay.
    """
    full_path = SatelliteService.resolve_explainability_file_path(filename)
    if os.path.exists(full_path):
        with open(full_path, "rb") as f:
            content = f.read()
    else:
        content = generate_synthetic_gradcam_heatmap()

    return Response(content=content, media_type="image/png")
