"""
Tests for health check endpoint.
"""
import pytest

@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert "version" in data
    assert "database" in data
    assert data["database"]["status"] == "connected"
    assert "services" in data
    assert "ml_detection" in data["services"]
    assert "ml_prediction" in data["services"]
