"""
Tests for cyclone listing and GeoJSON track generation endpoints.
"""
import pytest

@pytest.mark.asyncio
async def test_list_cyclones(client):
    response = await client.get("/cyclones")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    
    # Check attributes of seeded Active System
    active_cyclone = next((c for c in data if c["id"] == "CYC-2026-NIO-DEMO"), None)
    assert active_cyclone is not None
    assert active_cyclone["name"] == "Active System 01A"
    assert active_cyclone["basin"] == "Bay of Bengal"
    assert active_cyclone["latest_classification"] is not None

@pytest.mark.asyncio
async def test_get_cyclone_by_id(client):
    response = await client.get("/cyclones/CYC-2026-NIO-DEMO")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "CYC-2026-NIO-DEMO"
    assert data["name"] == "Active System 01A"

@pytest.mark.asyncio
async def test_get_cyclone_not_found(client):
    response = await client.get("/cyclones/NON_EXISTENT_CYC")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_track_geojson(client):
    response = await client.get("/cyclones/CYC-2026-NIO-DEMO/track-geojson")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert "features" in data
    assert len(data["features"]) > 0

    # Ensure observed line and observed points exist
    types = [f["properties"]["type"] for f in data["features"]]
    assert "observation" in types
    assert "observed_track" in types

    # Validate provenance separation guarantee
    provenances = set(f["properties"]["data_provenance"] for f in data["features"])
    assert "GROUND_TRUTH_OBSERVED" in provenances
