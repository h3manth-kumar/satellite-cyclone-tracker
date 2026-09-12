"""Training and evaluation modules."""

from src.training.dataset import CycloneDataset, generate_synthetic_satellite_image
from src.training.train import train_baseline_model
from src.training.evaluate import evaluate_model

__all__ = [
    "CycloneDataset",
    "generate_synthetic_satellite_image",
    "train_baseline_model",
    "evaluate_model",
]
