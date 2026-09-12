"""
API integration tests using FastAPI TestClient.
Tests endpoints: /health, /forecast, /track, /intensity and error cases.
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def get_sample_observations():
    return [
        {
            "timestamp": "2023-05-15T00:00:00Z",
            "latitude": 12.0,
            "longitude": 85.0,
            "wind_speed": 40.0,
            "pressure": 998.0,
        },
        {
            "timestamp": "2023-05-15T06:00:00Z",
            "latitude": 12.8,
            "longitude": 85.4,
            "wind_speed": 50.0,
            "pressure": 992.0,
        },
        {
            "timestamp": "2023-05-15T12:00:00Z",
            "latitude": 13.6,
            "longitude": 85.9,
            "wind_speed": 65.0,
            "pressure": 984.0,
        },
        {
            "timestamp": "2023-05-15T18:00:00Z",
            "latitude": 14.5,
            "longitude": 86.3,
            "wind_speed": 75.0,
            "pressure": 976.0,
        },
    ]


def test_api_health():
    with TestClient(app) as c:
        response = c.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "ml-prediction"
        assert "model_version" in data


def test_api_forecast_success():
    with TestClient(app) as c:
        payload = {
            "cyclone_id": "TEST_CYCLONE",
            "observations": get_sample_observations(),
        }
        response = c.post("/forecast", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["cyclone_id"] == "TEST_CYCLONE"
        assert "forecast_time" in data
        assert len(data["predictions"]) == 4

        for p in data["predictions"]:
            assert p["hours"] in [6, 12, 24, 48]
            assert -90.0 <= p["latitude"] <= 90.0
            assert -180.0 <= p["longitude"] <= 180.0
            assert 0.0 <= p["confidence"] <= 1.0
            assert p["error_radius_km"] > 0


def test_api_track_success():
    with TestClient(app) as c:
        payload = {
            "cyclone_id": "TEST_CYCLONE",
            "observations": get_sample_observations(),
        }
        response = c.post("/track", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert len(data["predictions"]) == 4
        assert "latitude" in data["predictions"][0]
        assert "error_radius_km" in data["predictions"][0]


def test_api_intensity_success():
    with TestClient(app) as c:
        payload = {
            "cyclone_id": "TEST_CYCLONE",
            "observations": get_sample_observations(),
        }
        response = c.post("/intensity", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert len(data["predictions"]) == 4
        assert "predicted_wind_speed" in data["predictions"][0]
        assert "predicted_pressure" in data["predictions"][0]


def test_api_insufficient_observations():
    with TestClient(app) as c:
        payload = {
            "cyclone_id": "TEST_FAIL",
            "observations": [
                {
                    "timestamp": "2023-05-15T00:00:00Z",
                    "latitude": 12.0,
                    "longitude": 85.0,
                }
            ],
        }
        response = c.post("/forecast", json=payload)
        # Should fail validation (min_length=2)
        assert response.status_code == 422


def test_api_invalid_coordinates():
    with TestClient(app) as c:
        obs = get_sample_observations()
        obs[0]["latitude"] = 120.0  # Invalid latitude > 90
        payload = {"cyclone_id": "TEST_FAIL", "observations": obs}
        response = c.post("/forecast", json=payload)
        assert response.status_code == 422


def test_api_missing_intensity_observations():
    """
    Verifies that when input observations lack wind/pressure labels,
    the model does NOT fabricate intensity predictions (returns None/null).
    """
    with TestClient(app) as c:
        obs = [
            {"timestamp": "2023-05-15T00:00:00Z", "latitude": 12.0, "longitude": 85.0},
            {"timestamp": "2023-05-15T06:00:00Z", "latitude": 12.8, "longitude": 85.4},
        ]
        payload = {"cyclone_id": "TEST_NO_INTENSITY", "observations": obs}
        response = c.post("/forecast", json=payload)
        assert response.status_code == 200
        data = response.json()
        for p in data["predictions"]:
            assert p["latitude"] is not None
            assert p["longitude"] is not None
            assert p["predicted_wind_speed"] is None
            assert p["predicted_pressure"] is None

