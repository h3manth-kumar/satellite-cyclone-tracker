"""
Uncertainty quantification and confidence estimation module.
Implements:
1. Monte Carlo Dropout (MCDO) sampling for epistemic uncertainty.
2. 95% Error Cone of Uncertainty calculation (in km).
3. Horizon-decayed calibrated confidence scoring.
"""

from typing import Dict, Any, List, Tuple
import numpy as np
import torch
import torch.nn as nn

KM_PER_DEGREE = 111.32  # Approximate km per degree latitude


class UncertaintyEstimator:
    """
    Defensible uncertainty estimator based on Monte Carlo Dropout (MCDO).
    Runs N stochastic forward passes with dropout active to estimate predictive variance.
    """

    def __init__(
        self,
        num_mc_samples: int = 25,
        horizon_hours: List[int] = None,
        base_decay_alpha: float = 0.45,
        spread_decay_beta: float = 0.35,
    ):
        self.num_mc_samples = num_mc_samples
        self.horizon_hours = horizon_hours or [6, 12, 24, 48]
        self.alpha = base_decay_alpha
        self.beta = spread_decay_beta

    def estimate(
        self,
        model: nn.Module,
        x: torch.Tensor,
        curr_state: torch.Tensor,
    ) -> Dict[str, np.ndarray]:
        """
        Runs Monte Carlo Dropout forward passes.
        Inputs:
          model: CycloneTrackGRU instance
          x: [B, seq_len, num_features]
          curr_state: [B, 4] -> [lat, lon, wind, pres]
        Returns dict of numpy arrays:
          mean_track: [B, num_horizons, 2]
          mean_intensity: [B, num_horizons, 2]
          error_radius_km: [B, num_horizons]
          confidence: [B, num_horizons]
          track_std: [B, num_horizons, 2]
          intensity_std: [B, num_horizons, 2]
        """
        device = next(model.parameters()).device
        x = x.to(device)
        curr_state = curr_state.to(device)

        mc_tracks = []
        mc_intensities = []

        with torch.no_grad():
            for _ in range(self.num_mc_samples):
                pred_track, pred_intensity = model.predict_absolute(
                    x, curr_state, enable_mc_dropout=True
                )
                mc_tracks.append(pred_track.cpu().numpy())
                mc_intensities.append(pred_intensity.cpu().numpy())

        # Reset model back to eval mode
        model.eval()

        # Stack to [N_samples, B, num_horizons, 2]
        stacked_tracks = np.stack(mc_tracks, axis=0)
        stacked_intensities = np.stack(mc_intensities, axis=0)

        # Means and Standard Deviations
        mean_track = np.mean(stacked_tracks, axis=0)  # [B, num_horizons, 2]
        mean_intensity = np.mean(stacked_intensities, axis=0)  # [B, num_horizons, 2]

        track_std = np.std(stacked_tracks, axis=0)  # [B, num_horizons, 2]
        intensity_std = np.std(stacked_intensities, axis=0)  # [B, num_horizons, 2]

        batch_size, n_horizons, _ = mean_track.shape
        error_radius_km = np.zeros((batch_size, n_horizons), dtype=np.float32)
        confidence = np.zeros((batch_size, n_horizons), dtype=np.float32)

        ref_radius = 180.0  # Reference spread radius in km for normalization

        for h_idx, hours in enumerate(self.horizon_hours):
            # Spatial standard deviation in degrees
            sigma_lat = track_std[:, h_idx, 0]
            sigma_lon = track_std[:, h_idx, 1]

            # Convert spatial standard deviation to distance in kilometers
            # Average cosine scaling for longitude at ~15 degrees latitude
            cos_factor = np.cos(np.radians(15.0))
            sigma_km = np.sqrt(sigma_lat**2 + (sigma_lon * cos_factor) ** 2) * KM_PER_DEGREE

            # 95% Confidence Cone radius: 1.96 * sigma, with a baseline minimum uncertainty
            # that expands realistically with time (e.g. at least ~30km at 6h up to ~120km at 48h)
            min_cone_radius = 25.0 + (hours / 48.0) * 80.0
            r_km = np.maximum(1.96 * sigma_km, min_cone_radius)
            error_radius_km[:, h_idx] = r_km

            # Confidence decays as lead-time increases and as epistemic variance widens
            # Bounded between 0.15 and 0.95
            decay_lead = self.alpha * (hours / 48.0)
            decay_variance = self.beta * (r_km / ref_radius)
            conf = np.exp(-(decay_lead + decay_variance))
            conf = np.clip(conf, 0.15, 0.95)
            confidence[:, h_idx] = conf

        return {
            "mean_track": mean_track,
            "mean_intensity": mean_intensity,
            "error_radius_km": error_radius_km,
            "confidence": confidence,
            "track_std": track_std,
            "intensity_std": intensity_std,
        }
