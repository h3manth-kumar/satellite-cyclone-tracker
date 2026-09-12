"""
Recurrent Neural Network (GRU) for Spatiotemporal Cyclone Track and Intensity Prediction.
Features:
- Multi-horizon direct prediction (+6h, +12h, +24h, +48h)
- Independent multi-head architecture for track displacement and intensity changes
- Monte Carlo Dropout support for epistemic uncertainty quantification
"""

from typing import Dict, Tuple, Optional, List
import torch
import torch.nn as nn
import torch.nn.functional as F


class CycloneTrackGRU(nn.Module):
    """
    Sequence-to-sequence multi-horizon GRU network.
    Inputs:
      x: [B, seq_len=4, input_dim=12]
      curr_state: [B, 4] -> [lat_t, lon_t, wind_t, pres_t]
    Outputs:
      track_disp: [B, num_horizons=4, 2] -> [delta_lat, delta_lon]
      intensity_disp: [B, num_horizons=4, 2] -> [delta_wind, delta_pres]
    """

    def __init__(
        self,
        input_dim: int = 12,
        hidden_dim: int = 64,
        num_layers: int = 2,
        num_horizons: int = 4,
        dropout: float = 0.20,
    ):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.num_horizons = num_horizons
        self.dropout_rate = dropout
        self.version = "track-model-v1.0"

        # Bidirectional or multilayer GRU encoder
        self.gru = nn.GRU(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )

        self.latent_dropout = nn.Dropout(p=dropout)

        # Head 1: Dedicated Track Displacement MLP Head
        self.track_head = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Dropout(p=dropout),
            nn.Linear(64, num_horizons * 2),
        )

        # Head 2: Dedicated Intensity Changes MLP Head
        self.intensity_head = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Dropout(p=dropout),
            nn.Linear(64, num_horizons * 2),
        )

    def forward(
        self, x: torch.Tensor, enable_mc_dropout: bool = False
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass.
        If enable_mc_dropout is True, forces dropout layers to stay active during eval mode.
        """
        if enable_mc_dropout:
            self.train()  # Activates dropout for Monte Carlo sampling

        # x: [B, seq_len, input_dim]
        out, h_n = self.gru(x)

        # Use last hidden state: [B, hidden_dim]
        last_hidden = h_n[-1]
        latent = self.latent_dropout(last_hidden)

        # Track displacements: [B, num_horizons, 2]
        track_raw = self.track_head(latent)
        track_disp = track_raw.view(-1, self.num_horizons, 2)

        # Intensity displacements: [B, num_horizons, 2]
        intensity_raw = self.intensity_head(latent)
        intensity_disp = intensity_raw.view(-1, self.num_horizons, 2)

        return {
            "track_disp": track_disp,
            "intensity_disp": intensity_disp,
        }

    def predict_absolute(
        self,
        x: torch.Tensor,
        curr_state: torch.Tensor,
        enable_mc_dropout: bool = False,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Computes absolute track coordinates and absolute intensity.
        curr_state: [B, 4] -> [lat, lon, wind, pres]
        Returns:
          abs_track: [B, num_horizons, 2] -> [pred_lat, pred_lon]
          abs_intensity: [B, num_horizons, 2] -> [pred_wind, pred_pres]
        """
        outputs = self.forward(x, enable_mc_dropout=enable_mc_dropout)
        track_disp = outputs["track_disp"]
        intensity_disp = outputs["intensity_disp"]

        # Current values unsqueezed: [B, 1, 2]
        curr_lat_lon = curr_state[:, :2].unsqueeze(1)
        curr_wind_pres = curr_state[:, 2:].unsqueeze(1)

        abs_track = curr_lat_lon + track_disp
        abs_intensity = curr_wind_pres + intensity_disp

        # Physical clamping
        abs_track[:, :, 0] = torch.clamp(abs_track[:, :, 0], -90.0, 90.0)
        abs_track[:, :, 1] = torch.clamp(abs_track[:, :, 1], -180.0, 180.0)

        # Wind speed >= 0, pressure between 850 and 1050
        abs_intensity[:, :, 0] = torch.clamp(abs_intensity[:, :, 0], min=0.0)
        abs_intensity[:, :, 1] = torch.clamp(abs_intensity[:, :, 1], min=850.0, max=1050.0)

        return abs_track, abs_intensity
