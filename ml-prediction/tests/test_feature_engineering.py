"""
Unit tests for feature engineering, Haversine metrics, and bearing calculations.
"""

import pytest
import numpy as np
import pandas as pd
from data.features import (
    haversine_distance,
    compute_bearing,
    extract_kinematic_features,
    extract_features_from_sequence,
)


def test_haversine_identical_points():
    dist = haversine_distance(15.0, 85.0, 15.0, 85.0)
    assert dist == pytest.approx(0.0, abs=1e-3)


def test_haversine_known_distance():
    # Chennai (13.0827, 80.2707) to Kolkata (22.5726, 88.3639) is approximately 1366 km
    dist = haversine_distance(13.0827, 80.2707, 22.5726, 88.3639)
    assert dist == pytest.approx(1366.0, rel=0.03)


def test_compute_bearing_cardinal_directions():
    # Due North
    b_north = compute_bearing(10.0, 80.0, 15.0, 80.0)
    assert b_north == pytest.approx(0.0, abs=1.0)

    # Due East
    b_east = compute_bearing(10.0, 80.0, 10.0, 85.0)
    assert b_east == pytest.approx(90.0, abs=1.0)

    # Due South
    b_south = compute_bearing(15.0, 80.0, 10.0, 80.0)
    assert b_south == pytest.approx(180.0, abs=1.0)

    # Due West
    b_west = compute_bearing(10.0, 85.0, 10.0, 80.0)
    assert b_west == pytest.approx(270.0, abs=1.0)


def test_extract_kinematic_features():
    df = pd.DataFrame({
        "cyclone_id": ["C1", "C1", "C1"],
        "timestamp": pd.to_datetime([
            "2023-06-01 00:00:00",
            "2023-06-01 06:00:00",
            "2023-06-01 12:00:00",
        ], utc=True),
        "latitude": [10.0, 11.0, 12.5],
        "longitude": [80.0, 80.5, 81.2],
        "wind_speed": [35.0, 45.0, 60.0],
        "pressure": [1000.0, 994.0, 986.0],
    })

    feat_df = extract_kinematic_features(df)

    assert "forward_speed_kmh" in feat_df.columns
    assert "bearing_sin" in feat_df.columns
    assert "bearing_cos" in feat_df.columns
    assert "delta_wind" in feat_df.columns
    assert "delta_pressure" in feat_df.columns

    # Speeds must be non-negative
    assert (feat_df["forward_speed_kmh"] >= 0).all()
    # Check delta_wind for second step: 45 - 35 = 10
    assert feat_df["delta_wind"].iloc[1] == pytest.approx(10.0)
    # Check delta_pressure for second step: 994 - 1000 = -6
    assert feat_df["delta_pressure"].iloc[1] == pytest.approx(-6.0)


def test_extract_features_from_sequence():
    observations = [
        {"timestamp": "2023-05-01T00:00:00Z", "latitude": 12.0, "longitude": 85.0, "wind_speed": 40.0, "pressure": 998.0},
        {"timestamp": "2023-05-01T06:00:00Z", "latitude": 12.8, "longitude": 85.3, "wind_speed": 50.0, "pressure": 992.0},
        {"timestamp": "2023-05-01T12:00:00Z", "latitude": 13.6, "longitude": 85.7, "wind_speed": 65.0, "pressure": 984.0},
    ]
    feat_matrix = extract_features_from_sequence(observations)
    assert isinstance(feat_matrix, np.ndarray)
    assert feat_matrix.shape == (3, 12)
    assert not np.isnan(feat_matrix).any()
