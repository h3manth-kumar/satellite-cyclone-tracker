"""
Tests for AI analysis endpoints and full multi-service pipeline orchestration.
"""
import pytest

@pytest.mark.asyncio
async def test_detect_endpoint(client):
    response = await client.post("/analysis/detect", json={
        "image_id": "SAT-INSAT3D-20260904-1200",
        "sensor": "TIR1"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["detected"] is True
    assert "latitude" in data
    assert "longitude" in data
    assert data["confidence"] > 0.5
    assert "model_version" in data

@pytest.mark.asyncio
async def test_classify_endpoint(client):
    response = await client.post("/analysis/classify", json={
        "image_id": "SAT-INSAT3D-20260904-1200",
        "latitude": 17.2,
        "longitude": 87.3
    })
    assert response.status_code == 200
    data = response.json()
    assert "classification" in data
    assert "confidence" in data
    assert "estimated_wind_speed" in data
    assert data["estimated_wind_speed"] > 0

@pytest.mark.asyncio
async def test_forecast_endpoint(client):
    response = await client.post("/analysis/forecast", json={
        "cyclone_id": "CYC-2026-NIO-DEMO",
        "history": [
            {"timestamp": "2026-09-04T06:00:00Z", "latitude": 16.7, "longitude": 87.0, "wind_speed": 70.0, "pressure": 976.0},
            {"timestamp": "2026-09-04T12:00:00Z", "latitude": 17.2, "longitude": 87.3, "wind_speed": 75.0, "pressure": 972.0}
        ]
    })
    assert response.status_code == 200
    data = response.json()
    assert data["cyclone_id"] == "CYC-2026-NIO-DEMO"
    assert len(data["forecast_points"]) >= 3
    first_pt = data["forecast_points"][0]
    assert first_pt["lead_hours"] == 6
    assert "predicted_wind_speed" in first_pt
    assert "predicted_pressure" in first_pt
    assert "uncertainty_radius_km" in first_pt

@pytest.mark.asyncio
async def test_full_analysis_pipeline(client):
    response = await client.post("/analysis/full", json={
        "cyclone_id": "CYC-2026-NIO-DEMO",
        "satellite_image_id": "SAT-INSAT3D-20260904-1200",
        "persist_results": True
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("success", "partial_success")
    assert "cyclone" in data
    assert data["cyclone"]["id"] == "CYC-2026-NIO-DEMO"
    assert "detection" in data
    assert "classification" in data
    assert "forecast" in data
    assert len(data["forecast"]) >= 3
    assert "disclaimer" in data
    assert "Not an official meteorological warning" in data["disclaimer"]
