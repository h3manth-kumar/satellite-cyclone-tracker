"""
Integration tests for neural model inference and uncertainty estimation.
"""

import pytest
import torch
import numpy as np
from models.recurrent_track_model import CycloneTrackGRU
from models.uncertainty import UncertaintyEstimator


def test_model_forward_and_shapes():
    model = CycloneTrackGRU(input_dim=12, hidden_dim=32, num_layers=2, num_horizons=4)
    model.eval()

    batch_size = 2
    x = torch.randn(batch_size, 4, 12)
    outputs = model(x)

    assert "track_disp" in outputs
    assert "intensity_disp" in outputs

    assert outputs["track_disp"].shape == (batch_size, 4, 2)
    assert outputs["intensity_disp"].shape == (batch_size, 4, 2)


def test_model_predict_absolute_bounds():
    model = CycloneTrackGRU(input_dim=12, hidden_dim=32, num_layers=2, num_horizons=4)
    model.eval()

    batch_size = 3
    x = torch.randn(batch_size, 4, 12)
    curr_state = torch.tensor([
        [15.0, 85.0, 60.0, 980.0],
        [20.0, 68.0, 45.0, 995.0],
        [10.0, 88.0, 80.0, 960.0],
    ])

    abs_track, abs_intensity = model.predict_absolute(x, curr_state)

    assert abs_track.shape == (batch_size, 4, 2)
    assert abs_intensity.shape == (batch_size, 4, 2)

    # Check bounds
    assert (abs_track[:, :, 0] >= -90.0).all() and (abs_track[:, :, 0] <= 90.0).all()
    assert (abs_track[:, :, 1] >= -180.0).all() and (abs_track[:, :, 1] <= 180.0).all()
    assert (abs_intensity[:, :, 0] >= 0.0).all()
    assert (abs_intensity[:, :, 1] >= 850.0).all() and (abs_intensity[:, :, 1] <= 1050.0).all()


def test_uncertainty_estimator():
    model = CycloneTrackGRU(input_dim=12, hidden_dim=32, num_layers=2, num_horizons=4)
    estimator = UncertaintyEstimator(num_mc_samples=10)

    x = torch.randn(1, 4, 12)
    curr_state = torch.tensor([[15.0, 85.0, 60.0, 980.0]])

    results = estimator.estimate(model, x, curr_state)

    assert "mean_track" in results
    assert "error_radius_km" in results
    assert "confidence" in results

    radii = results["error_radius_km"][0]
    confs = results["confidence"][0]

    assert len(radii) == 4
    assert len(confs) == 4

    # All radii positive
    assert (radii > 0).all()
    # Confidence in [0.0, 1.0]
    assert (confs >= 0.0).all() and (confs <= 1.0).all()
    # Confidence should decay over horizons
    assert confs[0] >= confs[-1]


def test_model_registry_save_and_load(tmp_path):
    from sklearn.preprocessing import StandardScaler
    from models.model_registry import save_checkpoint, load_model_pipeline

    model = CycloneTrackGRU(input_dim=12, hidden_dim=32, num_layers=2, num_horizons=4)
    scaler = StandardScaler()
    scaler.fit(np.random.randn(20, 12))

    checkpoint_file = tmp_path / "test_ckpt.pt"
    save_checkpoint(model, scaler, filepath=checkpoint_file, metadata={"test": True})
    assert checkpoint_file.exists()

    loaded_model, loaded_scaler, unc_est, baseline = load_model_pipeline(checkpoint_file, device="cpu")
    assert loaded_model.hidden_dim == 32
    assert loaded_scaler.mean_ is not None
    assert np.allclose(scaler.mean_, loaded_scaler.mean_)

