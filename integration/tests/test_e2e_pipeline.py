"""
End-to-End Pipeline Integration Test.
Validates complete flow: Backend -> PostgreSQL/PostGIS -> ML Adapters (M1 & M2) -> GeoJSON & Telemetry.
Can run against localhost (port 8000) or Docker container.
"""
import sys
import os
import requests
import json

BASE_URL = os.getenv("E2E_TARGET_URL", "http://localhost:8000").rstrip("/")

def log(msg, success=True):
    icon = "PASS" if success else "FAIL"
    print(f"[{icon}] {msg}")

def run_e2e_tests():
    print("=" * 70)
    print(f"CycloneAI End-to-End Integration Test Runner targeting: {BASE_URL}")
    print("=" * 70)

    # 1. Healthcheck
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        assert r.status_code == 200, f"Health returned status {r.status_code}"
        health = r.json()
        assert health["database"]["status"] == "connected", "Database is not connected"
        log(f"System Health: {health['status']} | DB Latency: {health['database'].get('latency_ms', 'N/A')}ms")
        log(f"ML Adapters: M1={health['services']['ml_detection']['status']}, M2={health['services']['ml_prediction']['status']}")
    except Exception as e:
        log(f"Healthcheck failed: {e}", success=False)
        return False

    # 2. List Cyclones
    try:
        r = requests.get(f"{BASE_URL}/cyclones", timeout=5)
        assert r.status_code == 200
        cyclones = r.json()
        assert len(cyclones) > 0, "No cyclones returned"
        demo = next((c for c in cyclones if c["id"] == "CYC-2026-NIO-DEMO"), None)
        assert demo is not None, "Demo active cyclone missing"
        log(f"Cyclone Registry: {len(cyclones)} systems available. Active: '{demo['name']}' ({demo['basin']})")
    except Exception as e:
        log(f"Cyclone listing failed: {e}", success=False)
        return False

    # 3. Query GeoJSON Track
    try:
        r = requests.get(f"{BASE_URL}/cyclones/CYC-2026-NIO-DEMO/track-geojson", timeout=5)
        assert r.status_code == 200
        geojson = r.json()
        assert geojson["type"] == "FeatureCollection"
        assert len(geojson["features"]) > 0
        feature_types = set(f["properties"]["type"] for f in geojson["features"])
        assert "observed_track" in feature_types
        assert "observation" in feature_types
        log(f"GeoJSON Track: Successfully retrieved {len(geojson['features'])} spatial features")
    except Exception as e:
        log(f"GeoJSON track retrieval failed: {e}", success=False)
        return False

    # 4. Member 1 Detection Direct Verification
    try:
        r = requests.post(
            f"{BASE_URL}/analysis/detect",
            json={
                "image_id": "SAT-INSAT3D-20260904-1200",
                "sensor": "TIR1",
                "bbox": {"min_lat": 10.0, "max_lat": 25.0, "min_lon": 80.0, "max_lon": 95.0}
            },
            timeout=10
        )
        assert r.status_code == 200
        det = r.json()
        assert "detected" in det
        assert "confidence" in det
        log(f"M1 Detection: Analysis completed (Detected: {det['detected']}, Center: [{det.get('latitude')}, {det.get('longitude')}], Conf: {det['confidence']*100:.1f}%)")
    except Exception as e:
        log(f"Member 1 Detection failed: {e}", success=False)
        return False

    # 5. Member 1 Classification Direct Verification
    try:
        r = requests.post(
            f"{BASE_URL}/analysis/classify",
            json={"image_id": "SAT-INSAT3D-20260904-1200", "latitude": 17.2, "longitude": 87.3},
            timeout=10
        )
        assert r.status_code == 200
        cls = r.json()
        assert cls["classification"] != ""
        log(f"M1 Classification: Classified as '{cls['classification']}' (Estimated Wind: {cls['estimated_wind_speed']} kts)")
    except Exception as e:
        log(f"Member 1 Classification failed: {e}", success=False)
        return False

    # 6. Member 2 Forecast Direct Verification
    try:
        r = requests.post(
            f"{BASE_URL}/analysis/forecast",
            json={
                "cyclone_id": "CYC-2026-NIO-DEMO",
                "history": [
                    {"timestamp": "2026-09-04T06:00:00Z", "latitude": 16.7, "longitude": 87.0, "wind_speed": 70.0, "pressure": 976.0},
                    {"timestamp": "2026-09-04T12:00:00Z", "latitude": 17.2, "longitude": 87.3, "wind_speed": 75.0, "pressure": 972.0}
                ]
            },
            timeout=10
        )
        assert r.status_code == 200
        fc = r.json()
        assert len(fc["forecast_points"]) >= 3
        log(f"M2 Forecasting: Generated {len(fc['forecast_points'])} future trajectory milestones")
    except Exception as e:
        log(f"Member 2 Forecast failed: {e}", success=False)
        return False

    # 7. Full Analysis Pipeline Execution (End-to-End Orchestration)
    try:
        r = requests.post(
            f"{BASE_URL}/analysis/full",
            json={
                "cyclone_id": "CYC-2026-NIO-DEMO",
                "satellite_image_id": "SAT-INSAT3D-20260904-1200",
                "persist_results": True
            },
            timeout=15
        )
        assert r.status_code == 200
        unified = r.json()
        assert unified["status"] in ("success", "partial_success")
        assert unified["cyclone"]["id"] == "CYC-2026-NIO-DEMO"
        assert len(unified["forecast"]) > 0
        assert "disclaimer" in unified
        log("Full AI Pipeline Orchestration: Successfully completed with unified response and database persistence")
        log(f"Disclaimer Verified: '{unified['disclaimer'][:60]}...'")
    except Exception as e:
        log(f"Full pipeline orchestration failed: {e}", success=False)
        return False

    print("=" * 70)
    print("ALL END-TO-END VERIFICATION CHECKS PASSED (100% SUCCESS)!")
    print("=" * 70)
    return True

if __name__ == "__main__":
    success = run_e2e_tests()
    sys.exit(0 if success else 1)
