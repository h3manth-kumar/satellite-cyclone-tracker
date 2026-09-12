"""
Data validation, cleaning, and temporal regularization module for cyclone observation data.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
import logging
import numpy as np
import pandas as pd

logger = logging.getLogger("DataCleaner")

# North Indian Ocean spatial bounding box
NIO_LAT_MIN, NIO_LAT_MAX = 0.0, 45.0
NIO_LON_MIN, NIO_LON_MAX = 45.0, 115.0


def validate_coordinates(lat: float, lon: float, strict_nio: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Validates geographical coordinates.
    """
    if not isinstance(lat, (int, float)) or np.isnan(lat):
        return False, f"Invalid latitude value: {lat}"
    if not isinstance(lon, (int, float)) or np.isnan(lon):
        return False, f"Invalid longitude value: {lon}"

    if not (-90.0 <= lat <= 90.0):
        return False, f"Latitude {lat} out of valid bounds [-90, 90]"
    if not (-180.0 <= lon <= 180.0):
        return False, f"Longitude {lon} out of valid bounds [-180, 180]"

    if strict_nio:
        if not (NIO_LAT_MIN <= lat <= NIO_LAT_MAX):
            return False, f"Latitude {lat} outside North Indian Ocean domain [{NIO_LAT_MIN}, {NIO_LAT_MAX}]"
        if not (NIO_LON_MIN <= lon <= NIO_LON_MAX):
            return False, f"Longitude {lon} outside North Indian Ocean domain [{NIO_LON_MIN}, {NIO_LON_MAX}]"

    return True, None


def validate_observation_dict(obs: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validates a single observation record from API requests or streaming input.
    """
    if "latitude" not in obs or "longitude" not in obs:
        return False, "Observation missing required 'latitude' or 'longitude' field"
    if "timestamp" not in obs:
        return False, "Observation missing required 'timestamp' field"

    valid_coords, err = validate_coordinates(obs["latitude"], obs["longitude"])
    if not valid_coords:
        return False, err

    try:
        ts = obs["timestamp"]
        if isinstance(ts, str):
            pd.to_datetime(ts)
    except Exception as e:
        return False, f"Invalid timestamp format: {obs['timestamp']} ({e})"

    if "wind_speed" in obs and obs["wind_speed"] is not None:
        ws = obs["wind_speed"]
        if ws < 0 or ws > 250:
            return False, f"Wind speed {ws} kt is outside physically plausible range [0, 250]"

    if "pressure" in obs and obs["pressure"] is not None:
        p = obs["pressure"]
        if p < 850 or p > 1050:
            return False, f"Pressure {p} hPa is outside physically plausible range [850, 1050]"

    return True, None


def clean_cyclone_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans and standardizes raw IBTrACS / IMD Best Track dataframe.
    """
    df = df.copy()

    # Standardize column names
    col_map = {
        "ISO_TIME": "timestamp",
        "LAT": "latitude",
        "LON": "longitude",
        "WMO_WIND": "wind_speed",
        "WMO_PRES": "pressure",
        "SID": "cyclone_id",
        "NAME": "cyclone_name",
    }
    rename_dict = {k: v for k, v in col_map.items() if k in df.columns}
    df = df.rename(columns=rename_dict)

    required_cols = ["timestamp", "latitude", "longitude"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' missing from dataframe")

    if "cyclone_id" not in df.columns:
        df["cyclone_id"] = "DEFAULT_CYCLONE"

    # Ensure correct data types
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

    if "wind_speed" in df.columns:
        df["wind_speed"] = pd.to_numeric(df["wind_speed"], errors="coerce")
        # Replace missing flags (-999, negative) with NaN
        df.loc[df["wind_speed"] < 0, "wind_speed"] = np.nan
    else:
        df["wind_speed"] = np.nan

    if "pressure" in df.columns:
        df["pressure"] = pd.to_numeric(df["pressure"], errors="coerce")
        # Replace invalid pressure with NaN
        df.loc[(df["pressure"] < 800) | (df["pressure"] > 1050), "pressure"] = np.nan
    else:
        df["pressure"] = np.nan

    # Drop records with invalid coordinates or timestamps
    initial_len = len(df)
    df = df.dropna(subset=["timestamp", "latitude", "longitude"])
    df = df[(df["latitude"].between(-90, 90)) & (df["longitude"].between(-180, 180))]

    # Sort strictly chronologically per cyclone
    df = df.sort_values(by=["cyclone_id", "timestamp"]).reset_index(drop=True)

    # Drop exact duplicate timestamps per storm
    df = df.drop_duplicates(subset=["cyclone_id", "timestamp"], keep="last")

    cleaned_len = len(df)
    logger.info(f"Cleaned dataset: {initial_len} -> {cleaned_len} records (dropped {initial_len - cleaned_len})")

    return df


def regularize_synoptic_intervals(df: pd.DataFrame, freq_hours: int = 6) -> pd.DataFrame:
    """
    Resamples and aligns storm tracks to regular synoptic intervals (00, 06, 12, 18 UTC).
    Performs linear interpolation for gaps <= 12 hours.
    """
    regularized_chunks = []

    for cid, group in df.groupby("cyclone_id"):
        group = group.set_index("timestamp").sort_index()

        # Resample onto synoptic grid
        rule = f"{freq_hours}h"
        resampled = group.resample(rule).asfreq()

        # Time delta in hours from previous observation
        time_diff = group.index.to_series().diff().dt.total_seconds() / 3600.0

        # Interpolate latitude and longitude for missing synoptic fixes (max limit 2 steps = 12 hours)
        resampled["latitude"] = resampled["latitude"].interpolate(method="time", limit=2)
        resampled["longitude"] = resampled["longitude"].interpolate(method="time", limit=2)

        if "wind_speed" in resampled.columns:
            resampled["wind_speed"] = resampled["wind_speed"].interpolate(method="time", limit=2)
        if "pressure" in resampled.columns:
            resampled["pressure"] = resampled["pressure"].interpolate(method="time", limit=2)

        resampled["cyclone_id"] = cid
        if "cyclone_name" in group.columns and not group["cyclone_name"].dropna().empty:
            resampled["cyclone_name"] = group["cyclone_name"].dropna().iloc[0]

        # Reset index to restore timestamp column
        resampled = resampled.reset_index()
        # Drop rows where coordinates could not be interpolated
        resampled = resampled.dropna(subset=["latitude", "longitude"])

        regularized_chunks.append(resampled)

    if not regularized_chunks:
        return df

    return pd.concat(regularized_chunks, ignore_index=True)
