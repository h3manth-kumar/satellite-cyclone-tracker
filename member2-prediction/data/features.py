"""
Feature engineering module for cyclone trajectory, kinematics, and intensity.
"""

from typing import List, Dict, Any, Tuple
import numpy as np
import pandas as pd

EARTH_RADIUS_KM = 6371.0


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes the great-circle distance between two points on the Earth's surface
    using the Haversine formula (returns distance in kilometers).
    """
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)

    a = (
        np.sin(delta_phi / 2.0) ** 2
        + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * np.arcsin(np.clip(np.sqrt(a), 0.0, 1.0))
    return float(EARTH_RADIUS_KM * c)


def compute_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes initial compass bearing (forward azimuth) in degrees [0, 360)
    from point 1 to point 2.
    """
    if abs(lat1 - lat2) < 1e-6 and abs(lon1 - lon2) < 1e-6:
        return 0.0

    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    delta_lambda = np.radians(lon2 - lon1)

    y = np.sin(delta_lambda) * np.cos(phi2)
    x = np.cos(phi1) * np.sin(phi2) - np.sin(phi1) * np.cos(phi2) * np.cos(delta_lambda)

    bearing_deg = (np.degrees(np.arctan2(y, x)) + 360.0) % 360.0
    return float(bearing_deg)


def extract_kinematic_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derives kinematic and spatial features for a cleaned dataframe of storm tracks.
    Assumes dataframe is sorted by cyclone_id and timestamp.
    """
    df = df.copy()

    # Displacements in degrees
    df["delta_lat"] = df.groupby("cyclone_id")["latitude"].diff().fillna(0.0)
    df["delta_lon"] = df.groupby("cyclone_id")["longitude"].diff().fillna(0.0)

    # Time step in hours
    time_diff_sec = df.groupby("cyclone_id")["timestamp"].diff().dt.total_seconds().fillna(6.0 * 3600.0)
    dt_hours = np.maximum(time_diff_sec / 3600.0, 0.1)

    # Distance, bearing and translation speed
    distances = []
    bearings = []

    for i in range(len(df)):
        if i == 0 or df["cyclone_id"].iloc[i] != df["cyclone_id"].iloc[i - 1]:
            # First point of a storm: zero displacement
            distances.append(0.0)
            bearings.append(0.0)
        else:
            lat1, lon1 = df["latitude"].iloc[i - 1], df["longitude"].iloc[i - 1]
            lat2, lon2 = df["latitude"].iloc[i], df["longitude"].iloc[i]
            d = haversine_distance(lat1, lon1, lat2, lon2)
            b = compute_bearing(lat1, lon1, lat2, lon2)
            distances.append(d)
            bearings.append(b)

    df["step_distance_km"] = distances
    df["bearing_deg"] = bearings
    df["forward_speed_kmh"] = df["step_distance_km"] / dt_hours

    # Cyclic bearing decomposition
    bearing_rad = np.radians(df["bearing_deg"])
    df["bearing_sin"] = np.sin(bearing_rad)
    df["bearing_cos"] = np.cos(bearing_rad)

    # Directional velocities (km/h)
    df["u_speed_kmh"] = df["forward_speed_kmh"] * df["bearing_sin"]
    df["v_speed_kmh"] = df["forward_speed_kmh"] * df["bearing_cos"]

    # Intensity tendencies
    if "wind_speed" in df.columns:
        df["delta_wind"] = df.groupby("cyclone_id")["wind_speed"].diff().fillna(0.0)
    else:
        df["delta_wind"] = 0.0

    if "pressure" in df.columns:
        df["delta_pressure"] = df.groupby("cyclone_id")["pressure"].diff().fillna(0.0)
    else:
        df["delta_pressure"] = 0.0

    return df


def extract_features_from_sequence(observations: List[Dict[str, Any]]) -> np.ndarray:
    """
    Extracts the numeric feature matrix [SeqLen, NumFeatures] from a raw observation list.
    Feature vector per timestep:
    [
        latitude,
        longitude,
        delta_lat,
        delta_lon,
        step_distance_km,
        forward_speed_kmh,
        bearing_sin,
        bearing_cos,
        wind_speed (or 0 if missing),
        delta_wind,
        pressure (or 1000 if missing),
        delta_pressure
    ]
    """
    if len(observations) < 1:
        raise ValueError("Observations list must contain at least 1 record.")

    records = []
    prev_obs = None

    for i, obs in enumerate(observations):
        lat = float(obs["latitude"])
        lon = float(obs["longitude"])
        wind = float(obs.get("wind_speed") or 0.0)
        pres = float(obs.get("pressure") or 1000.0)

        if prev_obs is None:
            delta_lat = 0.0
            delta_lon = 0.0
            dist = 0.0
            bearing = 0.0
            speed = 0.0
            delta_wind = 0.0
            delta_pres = 0.0
        else:
            prev_lat = float(prev_obs["latitude"])
            prev_lon = float(prev_obs["longitude"])
            prev_wind = float(prev_obs.get("wind_speed") or 0.0)
            prev_pres = float(prev_obs.get("pressure") or 1000.0)

            delta_lat = lat - prev_lat
            delta_lon = lon - prev_lon
            dist = haversine_distance(prev_lat, prev_lon, lat, lon)
            bearing = compute_bearing(prev_lat, prev_lon, lat, lon)

            # Compute time delta in hours if timestamps available
            dt_hours = 6.0
            if "timestamp" in obs and "timestamp" in prev_obs:
                try:
                    t1 = pd.to_datetime(prev_obs["timestamp"])
                    t2 = pd.to_datetime(obs["timestamp"])
                    diff_h = (t2 - t1).total_seconds() / 3600.0
                    if diff_h > 0.1:
                        dt_hours = diff_h
                except Exception:
                    pass

            speed = dist / dt_hours
            delta_wind = wind - prev_wind
            delta_pres = pres - prev_pres

        bearing_rad = np.radians(bearing)
        b_sin = np.sin(bearing_rad)
        b_cos = np.cos(bearing_rad)

        feat_vector = [
            lat,
            lon,
            delta_lat,
            delta_lon,
            dist,
            speed,
            b_sin,
            b_cos,
            wind,
            delta_wind,
            pres,
            delta_pres,
        ]
        records.append(feat_vector)
        prev_obs = obs

    return np.array(records, dtype=np.float32)
