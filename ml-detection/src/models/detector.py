"""Cyclone Detection Component."""

from typing import Tuple, Optional
import torch
import torch.nn as nn
from src.models.baseline_cnn import CycloneBaselineCNN


class CycloneDetector:
    """High-level detector interface for evaluating cyclone presence."""
    def __init__(self, model: CycloneBaselineCNN, threshold: float = 0.5):
        self.model = model
        self.threshold = threshold

    def detect(self, tensor: torch.Tensor) -> Tuple[bool, float]:
        """
        Runs detection on preprocessed input tensor [1, C, H, W].
        Returns:
            (detected: bool, confidence: float)
        """
        self.model.eval()
        with torch.no_grad():
            outputs = self.model(tensor)
            prob = float(outputs["detection_prob"].item())
            detected = prob >= self.threshold
            confidence = round(prob if detected else 1.0 - prob, 4)
            return detected, confidence
