"""
Baseline forecasting models for cyclone track and intensity.
Implements:
1. Persistence / Last-Known-Motion (LKM) baseline
2. Linear Extrapolation baseline
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np


class PersistenceBaseline:
    """
    Standard meteorological benchmark: Persistence (Last-Known-Motion).
    Extrapolates instantaneous velocity forward in time:
      lat(t + k*6h) = lat(t) + k * (lat(t) - lat(t - 6h))
      lon(t + k*6h) = lon(t) + k * (lon(t) - lon(t - 6h))
      wind(t + k*6h) = wind(t)
      pressure(t + k*6h) = pressure(t)
    """

    def __init__(self, horizon_hours: Optional[List[int]] = None):
        self.horizon_hours = horizon_hours or [6, 12, 24, 48]
        self.version = "baseline-persistence-v1.0"

    def predict(self, observations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generates forecast for given historical observations.
        Requires at least 2 chronological observations.
        """
        if len(observations) < 2:
            raise ValueError("Persistence baseline requires at least 2 historical observations.")

        curr = observations[-1]
        prev = observations[-2]

        curr_lat, curr_lon = float(curr["latitude"]), float(curr["longitude"])
        prev_lat, prev_lon = float(prev["latitude"]), float(prev["longitude"])

        curr_wind = float(curr.get("wind_speed") or 0.0)
        curr_pres = float(curr.get("pressure") or 1000.0)

        # 6-hour displacement
        d_lat_6h = curr_lat - prev_lat
        d_lon_6h = curr_lon - prev_lon

        predictions = []
        for hours in self.horizon_hours:
            step_multiplier = hours / 6.0
            pred_lat = curr_lat + step_multiplier * d_lat_6h
            pred_lon = curr_lon + step_multiplier * d_lon_6h

            # Clip within physical geography bounds
            pred_lat = np.clip(pred_lat, -90.0, 90.0)
            pred_lon = np.clip(pred_lon, -180.0, 180.0)

            # Confidence decays strictly with lead time
            confidence = max(0.1, 0.95 - (hours / 48.0) * 0.50)
            # Baseline uncertainty radius grows with horizon (~60km per 24h)
            radius_km = 30.0 + (hours / 6.0) * 25.0

            predictions.append({
                "hours": hours,
                "latitude": round(float(pred_lat), 3),
                "longitude": round(float(pred_lon), 3),
                "predicted_wind_speed": round(curr_wind, 1) if curr_wind > 0 else None,
                "predicted_pressure": round(curr_pres, 1) if curr_pres > 800 else None,
                "confidence": round(float(confidence), 3),
                "error_radius_km": round(float(radius_km), 1),
            })

        return predictions

    def predict_tensor(
        self, curr_states: np.ndarray, prev_states: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Vectorized prediction for arrays/tensors.
        curr_states: [B, 4] -> [lat, lon, wind, pres]
        prev_states: [B, 4] -> [lat, lon, wind, pres]
        Returns:
          pred_tracks: [B, num_horizons, 2] -> [pred_lat, pred_lon]
          pred_intensity: [B, num_horizons, 2] -> [pred_wind, pred_pres]
        """
        batch_size = curr_states.shape[0]
        n_horizons = len(self.horizon_hours)

        pred_tracks = np.zeros((batch_size, n_horizons, 2), dtype=np.float32)
        pred_intensity = np.zeros((batch_size, n_horizons, 2), dtype=np.float32)

        d_lat = curr_states[:, 0] - prev_states[:, 0]
        d_lon = curr_states[:, 1] - prev_states[:, 1]

        for h_idx, hours in enumerate(self.horizon_hours):
            k = hours / 6.0
            pred_tracks[:, h_idx, 0] = curr_states[:, 0] + k * d_lat
            pred_tracks[:, h_idx, 1] = curr_states[:, 1] + k * d_lon
            pred_intensity[:, h_idx, 0] = curr_states[:, 2]
            pred_intensity[:, h_idx, 1] = curr_states[:, 3]

        return pred_tracks, pred_intensity
