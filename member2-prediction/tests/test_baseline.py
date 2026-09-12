"""
Unit tests for persistence and last-known-motion baseline model.
"""

import pytest
import numpy as np
from models.baseline import PersistenceBaseline


def test_persistence_baseline_extrapolation():
    baseline = PersistenceBaseline()

    observations = [
        {"latitude": 10.0, "longitude": 80.0, "wind_speed": 40.0, "pressure": 1000.0},
        {"latitude": 11.0, "longitude": 80.5, "wind_speed": 45.0, "pressure": 995.0},
    ]

    preds = baseline.predict(observations)
    assert len(preds) == 4

    p_6h = preds[0]
    assert p_6h["hours"] == 6
    assert p_6h["latitude"] == pytest.approx(12.0)
    assert p_6h["longitude"] == pytest.approx(81.0)
    assert p_6h["predicted_wind_speed"] == pytest.approx(45.0)

    p_12h = preds[1]
    assert p_12h["hours"] == 12
    assert p_12h["latitude"] == pytest.approx(13.0)
    assert p_12h["longitude"] == pytest.approx(81.5)

    p_24h = preds[2]
    assert p_24h["hours"] == 24
    assert p_24h["latitude"] == pytest.approx(15.0)
    assert p_24h["longitude"] == pytest.approx(82.5)

    p_48h = preds[3]
    assert p_48h["hours"] == 48
    assert p_48h["latitude"] == pytest.approx(19.0)
    assert p_48h["longitude"] == pytest.approx(84.5)

    # Check that error radius expands and confidence decays
    radii = [p["error_radius_km"] for p in preds]
    confs = [p["confidence"] for p in preds]
    assert radii == sorted(radii)
    assert confs == sorted(confs, reverse=True)


def test_persistence_baseline_insufficient_history():
    baseline = PersistenceBaseline()
    with pytest.raises(ValueError):
        baseline.predict([{"latitude": 10.0, "longitude": 80.0}])
