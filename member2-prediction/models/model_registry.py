"""
Model registry and serialization module.
Handles loading/saving of trained model weights, scalers, and inference components.
"""

from pathlib import Path
from typing import Tuple, Optional, Dict, Any
import logging
import numpy as np
import torch
from sklearn.preprocessing import StandardScaler

from models.recurrent_track_model import CycloneTrackGRU
from models.baseline import PersistenceBaseline
from models.uncertainty import UncertaintyEstimator

logger = logging.getLogger("ModelRegistry")

DEFAULT_CHECKPOINT_DIR = Path(__file__).resolve().parent.parent / "checkpoints"
DEFAULT_MODEL_FILE = DEFAULT_CHECKPOINT_DIR / "track_model_v1.pt"
MODEL_VERSION = "track-model-v1.0"


def save_checkpoint(
    model: CycloneTrackGRU,
    scaler: StandardScaler,
    filepath: Path = DEFAULT_MODEL_FILE,
    metadata: Optional[Dict[str, Any]] = None,
) -> Path:
    """
    Saves model weights, scaler statistics, and metadata.
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "model_state_dict": model.state_dict(),
        "model_config": {
            "input_dim": model.input_dim,
            "hidden_dim": model.hidden_dim,
            "num_layers": model.num_layers,
            "num_horizons": model.num_horizons,
            "dropout": model.dropout_rate,
            "version": MODEL_VERSION,
        },
        "scaler_mean": scaler.mean_,
        "scaler_scale": scaler.scale_,
        "metadata": metadata or {},
    }

    torch.save(payload, filepath)
    logger.info(f"Model checkpoint saved successfully to {filepath}")
    return filepath


def load_model_pipeline(
    checkpoint_path: Path = DEFAULT_MODEL_FILE,
    device: Optional[str] = None,
) -> Tuple[CycloneTrackGRU, StandardScaler, UncertaintyEstimator, PersistenceBaseline]:
    """
    Loads model, scaler, uncertainty estimator, and baseline.
    If no checkpoint exists, initializes a newly instantiated model with default statistics.
    """
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    baseline = PersistenceBaseline()
    uncertainty_estimator = UncertaintyEstimator()

    scaler = StandardScaler()

    if checkpoint_path.exists():
        logger.info(f"Loading checkpoint from: {checkpoint_path}")
        checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)

        cfg = checkpoint.get("model_config", {})
        model = CycloneTrackGRU(
            input_dim=cfg.get("input_dim", 12),
            hidden_dim=cfg.get("hidden_dim", 64),
            num_layers=cfg.get("num_layers", 2),
            num_horizons=cfg.get("num_horizons", 4),
            dropout=cfg.get("dropout", 0.20),
        )
        model.load_state_dict(checkpoint["model_state_dict"])

        # Restore scaler
        scaler.mean_ = checkpoint["scaler_mean"]
        scaler.scale_ = checkpoint["scaler_scale"]
        scaler.n_features_in_ = len(scaler.mean_)
    else:
        logger.warning(
            f"Checkpoint not found at {checkpoint_path}. Initializing default unweighted model."
        )
        model = CycloneTrackGRU(input_dim=12, hidden_dim=64, num_layers=2, num_horizons=4)
        # Default mock statistics for 12 features
        scaler.mean_ = np.zeros(12, dtype=np.float32)
        scaler.scale_ = np.ones(12, dtype=np.float32)
        scaler.n_features_in_ = 12

    model.to(device)
    model.eval()

    return model, scaler, uncertainty_estimator, baseline
