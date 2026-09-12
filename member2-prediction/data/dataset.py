"""
PyTorch Dataset and Sequence Generator for Cyclone Track & Intensity Forecasting.
Guarantees event-based storm partitioning with ZERO temporal or storm leakage.
"""

from typing import List, Tuple, Dict, Any, Optional
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset
from sklearn.preprocessing import StandardScaler

FEATURE_COLUMNS = [
    "latitude",
    "longitude",
    "delta_lat",
    "delta_lon",
    "step_distance_km",
    "forward_speed_kmh",
    "bearing_sin",
    "bearing_cos",
    "wind_speed",
    "delta_wind",
    "pressure",
    "delta_pressure",
]

# Step offsets for 6-hour data corresponding to horizons: +6h, +12h, +24h, +48h
HORIZON_STEPS = [1, 2, 4, 8]
HORIZON_HOURS = [6, 12, 24, 48]


def split_cyclones_by_event(
    df: pd.DataFrame,
    test_cyclone_ids: Optional[List[str]] = None,
    val_cyclone_ids: Optional[List[str]] = None,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Partitions the dataset strictly by cyclone identifier (event-based split).
    No individual storm is ever split across partitions.
    """
    unique_cyclones = df["cyclone_id"].unique().tolist()

    if test_cyclone_ids is not None:
        test_cids = set(test_cyclone_ids)
        val_cids = set(val_cyclone_ids) if val_cyclone_ids is not None else set()
        train_cids = [c for c in unique_cyclones if c not in test_cids and c not in val_cids]
    else:
        rng = np.random.default_rng(random_state)
        shuffled = unique_cyclones.copy()
        rng.shuffle(shuffled)

        n_total = len(shuffled)
        n_train = max(1, int(n_total * train_ratio))
        n_val = max(1, int(n_total * val_ratio))

        train_cids = shuffled[:n_train]
        val_cids = shuffled[n_train : n_train + n_val]
        test_cids = shuffled[n_train + n_val :]

        # Edge case: If few storms, ensure test set has at least one
        if len(test_cids) == 0 and len(train_cids) > 1:
            test_cids = [train_cids.pop()]

    train_df = df[df["cyclone_id"].isin(train_cids)].reset_index(drop=True)
    val_df = df[df["cyclone_id"].isin(val_cids)].reset_index(drop=True)
    test_df = df[df["cyclone_id"].isin(test_cids)].reset_index(drop=True)

    return train_df, val_df, test_df


class CycloneTrackDataset(Dataset):
    """
    Sliding-window sequence dataset.
    Given lookback L_in=4 steps (24 hours):
      X: [L_in, num_features]
      y_track_disp: [4, 2] -> [delta_lat, delta_lon] for horizons [+6h, +12h, +24h, +48h]
      y_intensity_disp: [4, 2] -> [delta_wind, delta_pressure]
      y_abs_track: [4, 2] -> [target_lat, target_lon]
      y_abs_intensity: [4, 2] -> [target_wind, target_pressure]
      mask: [4] -> 1.0 if horizon is valid in track, 0.0 if dissipated
    """

    def __init__(
        self,
        df: pd.DataFrame,
        scaler: Optional[StandardScaler] = None,
        fit_scaler: bool = False,
        lookback_steps: int = 4,
        horizon_steps: Optional[List[int]] = None,
    ):
        self.lookback_steps = lookback_steps
        self.horizon_steps = horizon_steps or HORIZON_STEPS
        self.df = df.copy()

        # Handle missing columns or NaN in features
        for col in FEATURE_COLUMNS:
            if col not in self.df.columns:
                self.df[col] = 0.0
            else:
                self.df[col] = self.df[col].fillna(0.0)

        # Scale features
        feature_matrix = self.df[FEATURE_COLUMNS].values.astype(np.float32)
        if fit_scaler:
            self.scaler = StandardScaler()
            self.scaler.fit(feature_matrix)
        else:
            self.scaler = scaler

        if self.scaler is not None:
            self.scaled_features = self.scaler.transform(feature_matrix)
        else:
            self.scaled_features = feature_matrix

        self.df["feat_idx"] = np.arange(len(self.df))

        # Build sequence indices
        self.samples = self._build_sliding_windows()

    def _build_sliding_windows(self) -> List[Dict[str, Any]]:
        samples = []

        for cid, group in self.df.groupby("cyclone_id"):
            group_indices = group["feat_idx"].values
            n_points = len(group_indices)

            # Need at least lookback_steps + 1 points to create at least one +6h prediction
            if n_points < self.lookback_steps + 1:
                continue

            max_future = max(self.horizon_steps)
            for i in range(self.lookback_steps - 1, n_points - 1):
                in_indices = group_indices[i - self.lookback_steps + 1 : i + 1]
                curr_idx = in_indices[-1]

                curr_lat = float(self.df.loc[curr_idx, "latitude"])
                curr_lon = float(self.df.loc[curr_idx, "longitude"])
                curr_wind = float(self.df.loc[curr_idx, "wind_speed"])
                curr_pres = float(self.df.loc[curr_idx, "pressure"])
                curr_time = self.df.loc[curr_idx, "timestamp"]

                # Target arrays for the 4 horizons
                track_disp = np.zeros((len(self.horizon_steps), 2), dtype=np.float32)
                intensity_disp = np.zeros((len(self.horizon_steps), 2), dtype=np.float32)
                abs_track = np.zeros((len(self.horizon_steps), 2), dtype=np.float32)
                abs_intensity = np.zeros((len(self.horizon_steps), 2), dtype=np.float32)
                target_times = []
                mask = np.zeros(len(self.horizon_steps), dtype=np.float32)
                intensity_mask = np.zeros(len(self.horizon_steps), dtype=np.float32)

                for h_idx, step_offset in enumerate(self.horizon_steps):
                    future_pos = i + step_offset
                    if future_pos < n_points:
                        fut_idx = group_indices[future_pos]
                        fut_lat = float(self.df.loc[fut_idx, "latitude"])
                        fut_lon = float(self.df.loc[fut_idx, "longitude"])
                        fut_wind = float(self.df.loc[fut_idx, "wind_speed"])
                        fut_pres = float(self.df.loc[fut_idx, "pressure"])

                        track_disp[h_idx] = [fut_lat - curr_lat, fut_lon - curr_lon]
                        intensity_disp[h_idx] = [fut_wind - curr_wind, fut_pres - curr_pres]
                        abs_track[h_idx] = [fut_lat, fut_lon]
                        abs_intensity[h_idx] = [fut_wind, fut_pres]
                        target_times.append(self.df.loc[fut_idx, "timestamp"])
                        mask[h_idx] = 1.0

                        # Intensity label is only valid if wind > 0 and pressure within plausible range
                        if fut_wind > 0.0 and (850.0 <= fut_pres <= 1050.0):
                            intensity_mask[h_idx] = 1.0
                    else:
                        target_times.append(None)

                # Store sample metadata and indices
                samples.append({
                    "in_indices": in_indices,
                    "curr_state": np.array([curr_lat, curr_lon, curr_wind, curr_pres], dtype=np.float32),
                    "curr_time": curr_time,
                    "track_disp": track_disp,
                    "intensity_disp": intensity_disp,
                    "abs_track": abs_track,
                    "abs_intensity": abs_intensity,
                    "mask": mask,
                    "intensity_mask": intensity_mask,
                    "cyclone_id": cid,
                })

        return samples

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        item = self.samples[idx]
        in_feats = self.scaled_features[item["in_indices"]]  # [lookback, num_features]

        return {
            "x": torch.tensor(in_feats, dtype=torch.float32),
            "curr_state": torch.tensor(item["curr_state"], dtype=torch.float32),
            "track_disp": torch.tensor(item["track_disp"], dtype=torch.float32),
            "intensity_disp": torch.tensor(item["intensity_disp"], dtype=torch.float32),
            "abs_track": torch.tensor(item["abs_track"], dtype=torch.float32),
            "abs_intensity": torch.tensor(item["abs_intensity"], dtype=torch.float32),
            "mask": torch.tensor(item["mask"], dtype=torch.float32),
            "intensity_mask": torch.tensor(item["intensity_mask"], dtype=torch.float32),
        }
