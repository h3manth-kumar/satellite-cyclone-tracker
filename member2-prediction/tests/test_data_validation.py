"""
Unit tests for data validation, coordinate sanitization, and cleaning.
"""

import pytest
import numpy as np
import pandas as pd
from data.cleaner import (
    validate_coordinates,
    validate_observation_dict,
    clean_cyclone_dataframe,
    regularize_synoptic_intervals,
)


def test_validate_coordinates_valid():
    ok, err = validate_coordinates(15.5, 85.2)
    assert ok is True
    assert err is None


def test_validate_coordinates_out_of_bounds():
    ok, err = validate_coordinates(95.0, 80.0)
    assert ok is False
    assert "Latitude" in err

    ok, err = validate_coordinates(15.0, 200.0)
    assert ok is False
    assert "Longitude" in err

    ok, err = validate_coordinates(np.nan, 80.0)
    assert ok is False


def test_validate_observation_dict():
    valid_obs = {
        "timestamp": "2023-06-06T06:00:00Z",
        "latitude": 12.5,
        "longitude": 68.0,
        "wind_speed": 45.0,
        "pressure": 995.0,
    }
    ok, err = validate_observation_dict(valid_obs)
    assert ok is True

    # Missing latitude
    invalid_obs = {"timestamp": "2023-06-06T06:00:00Z", "longitude": 68.0}
    ok, err = validate_observation_dict(invalid_obs)
    assert ok is False

    # Implausible pressure
    invalid_pres = {
        "timestamp": "2023-06-06T06:00:00Z",
        "latitude": 12.5,
        "longitude": 68.0,
        "pressure": 300.0,
    }
    ok, err = validate_observation_dict(invalid_pres)
    assert ok is False


def test_clean_cyclone_dataframe():
    raw_data = {
        "SID": ["CY1", "CY1", "CY1", "CY1", "CY2"],
        "ISO_TIME": [
            "2021-05-14 12:00:00",
            "2021-05-14 06:00:00",  # Unsorted
            "2021-05-14 12:00:00",  # Duplicate
            "2021-05-14 18:00:00",
            "2021-05-15 00:00:00",
        ],
        "LAT": [12.0, 11.0, 12.0, 13.0, 150.0],  # 150.0 is invalid coordinate
        "LON": [72.0, 71.5, 72.0, 72.5, 80.0],
        "WMO_WIND": [45.0, 35.0, 45.0, -999.0, 50.0],  # -999 is missing flag
        "WMO_PRES": [995.0, 1000.0, 995.0, 990.0, 990.0],
    }
    df = pd.DataFrame(raw_data)
    cleaned = clean_cyclone_dataframe(df)

    # Check that CY2 was dropped (lat 150)
    assert "CY2" not in cleaned["cyclone_id"].values
    # Check that duplicate CY1 timestamp was removed
    assert len(cleaned[cleaned["cyclone_id"] == "CY1"]) == 3
    # Check chronological ordering
    cy1_times = cleaned[cleaned["cyclone_id"] == "CY1"]["timestamp"].tolist()
    assert cy1_times == sorted(cy1_times)
    # Check missing wind flag was converted to NaN
    assert pd.isna(cleaned.loc[cleaned["timestamp"] == "2021-05-14 18:00:00", "wind_speed"].iloc[0])


def test_regularize_synoptic_intervals():
    df = pd.DataFrame({
        "cyclone_id": ["CY_ALIGN", "CY_ALIGN"],
        "timestamp": pd.to_datetime(["2023-05-15 00:00:00", "2023-05-15 12:00:00"], utc=True),
        "latitude": [10.0, 12.0],
        "longitude": [80.0, 82.0],
        "wind_speed": [40.0, 60.0],
        "pressure": [1000.0, 980.0],
    })
    reg_df = regularize_synoptic_intervals(df, freq_hours=6)
    # Should have interpolated a fix at 06:00:00
    assert len(reg_df) == 3
    mid_row = reg_df.iloc[1]
    assert mid_row["latitude"] == pytest.approx(11.0)
    assert mid_row["longitude"] == pytest.approx(81.0)
    assert mid_row["wind_speed"] == pytest.approx(50.0)
    assert mid_row["pressure"] == pytest.approx(990.0)
