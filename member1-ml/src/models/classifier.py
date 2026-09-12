"""Cyclone Stage/Intensity Classifier Component."""

from typing import Tuple, Dict, List, Optional
import torch
import torch.nn.functional as F
from src.models.baseline_cnn import CycloneBaselineCNN, IMD_CYCLONE_CLASSES


class CycloneClassifier:
    """High-level classifier interface for determining cyclone intensity stage."""
    def __init__(
        self,
        model: CycloneBaselineCNN,
        classes: Optional[List[str]] = None,
    ):
        self.model = model
        self.classes = classes or IMD_CYCLONE_CLASSES

    def classify(self, tensor: torch.Tensor) -> Tuple[str, float, Dict[str, float]]:
        """
        Runs intensity classification on preprocessed input tensor [1, C, H, W].
        Returns:
            (predicted_class: str, confidence: float, probabilities: dict)
        """
        self.model.eval()
        with torch.no_grad():
            outputs = self.model(tensor)
            probs = outputs["class_probs"][0].cpu().numpy()
            
            top_idx = int(probs.argmax())
            predicted_class = self.classes[top_idx]
            confidence = round(float(probs[top_idx]), 4)
            
            prob_dict = {
                self.classes[i]: round(float(probs[i]), 4)
                for i in range(min(len(self.classes), len(probs)))
            }
            
            return predicted_class, confidence, prob_dict
