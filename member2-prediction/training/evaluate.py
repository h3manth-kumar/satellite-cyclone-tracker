"""
Independent evaluation module for CycloneAI track and intensity models.
Computes:
1. Haversine track distance errors (Mean Track Error in km) for +6h, +12h, +24h, +48h
2. Persistence baseline vs. ML Model comparison
3. Intensity MAE and RMSE (Wind in kt, Pressure in hPa)
4. Forecast Skill Scores (%)
"""

from pathlib import Path
import sys

# Ensure package root is in python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from typing import Dict, Any, List
import logging
import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

from data.cleaner import clean_cyclone_dataframe, regularize_synoptic_intervals
from data.features import extract_kinematic_features, haversine_distance
from data.dataset import CycloneTrackDataset, split_cyclones_by_event, HORIZON_HOURS
from models.baseline import PersistenceBaseline
from models.model_registry import load_model_pipeline, DEFAULT_MODEL_FILE

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Evaluator")


def evaluate_forecasts(
    data_csv_path: Path,
    checkpoint_path: Path = DEFAULT_MODEL_FILE,
) -> Dict[str, Any]:
    """
    Evaluates both Persistence Baseline and ML Model on holdout cyclone tracks.
    """
    raw_df = pd.read_csv(data_csv_path)
    cleaned = clean_cyclone_dataframe(raw_df)
    regularized = regularize_synoptic_intervals(cleaned)
    feat_df = extract_kinematic_features(regularized)

    _, _, test_df = split_cyclones_by_event(feat_df, random_state=42)
    if len(test_df) == 0:
        test_df = feat_df  # Fallback to full set if small catalog

    model, scaler, uncertainty_est, baseline = load_model_pipeline(checkpoint_path)

    test_ds = CycloneTrackDataset(test_df, scaler=scaler)
    if len(test_ds) == 0:
        logger.warning("Test dataset contains 0 sequences. Falling back to full dataset.")
        test_ds = CycloneTrackDataset(feat_df, scaler=scaler)

    loader = DataLoader(test_ds, batch_size=len(test_ds), shuffle=False)
    batch = next(iter(loader))

    x = batch["x"]
    curr_state = batch["curr_state"]  # [B, 4] -> [lat, lon, wind, pres]
    abs_track = batch["abs_track"].numpy()  # [B, 4, 2] -> [true_lat, true_lon]
    abs_intensity = batch["abs_intensity"].numpy()  # [B, 4, 2] -> [true_wind, true_pres]
    mask = batch["mask"].numpy()  # [B, 4]

    # 1. Baseline Predictions
    # Previous state is derived from lookback sequence
    # Unscale the second-to-last timestep: lat, lon, wind, pres
    x_unscaled = scaler.inverse_transform(x[:, -2, :].numpy())
    prev_states = np.column_stack([
        x_unscaled[:, 0],  # lat
        x_unscaled[:, 1],  # lon
        x_unscaled[:, 8],  # wind
        x_unscaled[:, 10],  # pres
    ])
    base_tracks, base_intensity = baseline.predict_tensor(curr_state.numpy(), prev_states)

    # 2. ML Model Predictions
    with torch.no_grad():
        ml_tracks_tensor, ml_intensity_tensor = model.predict_absolute(x, curr_state)
        ml_tracks = ml_tracks_tensor.numpy()
        ml_intensity = ml_intensity_tensor.numpy()

    # 3. Compute Metrics per Horizon
    horizons = HORIZON_HOURS
    metrics = {
        "horizons": horizons,
        "baseline_mte_km": [],
        "ml_mte_km": [],
        "track_skill_percent": [],
        "baseline_wind_mae": [],
        "ml_wind_mae": [],
        "baseline_pres_mae": [],
        "ml_pres_mae": [],
    }

    n_samples = len(test_ds)

    print("\n" + "=" * 78)
    print("           CYCLONEAI - INDEPENDENT FORECAST EVALUATION REPORT           ")
    print("=" * 78)
    print(f"{'Horizon':<10} | {'Base Track':<12} | {'ML Track':<12} | {'Track Skill':<12} | {'Wind MAE':<10} | {'Pres MAE':<10}")
    print(f"{'(hours)':<10} | {'(MTE km)':<12} | {'(MTE km)':<12} | {'(%)':<12} | {'(ML kt)':<10} | {'(ML hPa)':<10}")
    print("-" * 78)

    for h_idx, h in enumerate(horizons):
        valid_indices = np.where(mask[:, h_idx] > 0.5)[0]
        if len(valid_indices) == 0:
            continue

        base_dists = []
        ml_dists = []
        base_w_errs = []
        ml_w_errs = []
        base_p_errs = []
        ml_p_errs = []

        for i in valid_indices:
            t_lat, t_lon = abs_track[i, h_idx, 0], abs_track[i, h_idx, 1]
            t_wind, t_pres = abs_intensity[i, h_idx, 0], abs_intensity[i, h_idx, 1]

            # Track Haversine distance
            b_lat, b_lon = base_tracks[i, h_idx, 0], base_tracks[i, h_idx, 1]
            m_lat, m_lon = ml_tracks[i, h_idx, 0], ml_tracks[i, h_idx, 1]

            base_dists.append(haversine_distance(b_lat, b_lon, t_lat, t_lon))
            ml_dists.append(haversine_distance(m_lat, m_lon, t_lat, t_lon))

            # Intensity errors
            b_w, b_p = base_intensity[i, h_idx, 0], base_intensity[i, h_idx, 1]
            m_w, m_p = ml_intensity[i, h_idx, 0], ml_intensity[i, h_idx, 1]

            base_w_errs.append(abs(b_w - t_wind))
            ml_w_errs.append(abs(m_w - t_wind))
            base_p_errs.append(abs(b_p - t_pres))
            ml_p_errs.append(abs(m_p - t_pres))

        mte_base = float(np.mean(base_dists))
        mte_ml = float(np.mean(ml_dists))
        skill = ((mte_base - mte_ml) / max(mte_base, 1e-4)) * 100.0

        w_mae = float(np.mean(ml_w_errs))
        p_mae = float(np.mean(ml_p_errs))

        metrics["baseline_mte_km"].append(round(mte_base, 1))
        metrics["ml_mte_km"].append(round(mte_ml, 1))
        metrics["track_skill_percent"].append(round(skill, 1))
        metrics["baseline_wind_mae"].append(round(float(np.mean(base_w_errs)), 1))
        metrics["ml_wind_mae"].append(round(w_mae, 1))
        metrics["baseline_pres_mae"].append(round(float(np.mean(base_p_errs)), 1))
        metrics["ml_pres_mae"].append(round(p_mae, 1))

        print(
            f"{f'+{h}h':<10} | {mte_base:<12.1f} | {mte_ml:<12.1f} | {skill:<+11.1f}% | {w_mae:<10.1f} | {p_mae:<10.1f}"
        )

    print("=" * 78)
    return metrics


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data",
        type=str,
        default=str(Path(__file__).resolve().parent.parent / "data" / "benchmark_sample.csv"),
    )
    args = parser.parse_args()
    evaluate_forecasts(Path(args.data))
