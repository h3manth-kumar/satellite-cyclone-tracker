"""End-to-end Cyclone Inference Engine."""

import os
import time
from typing import Dict, Any, Optional, Union, Tuple
from datetime import datetime, timezone
import torch
from PIL import Image

from src.models.baseline_cnn import CycloneBaselineCNN, IMD_CYCLONE_CLASSES
from src.models.detector import CycloneDetector
from src.models.classifier import CycloneClassifier
from src.models.center_locator import CycloneCenterLocator
from src.explainability.gradcam import GradCAM
from src.preprocessing.image_loader import validate_and_load_image
from src.preprocessing.transforms import preprocess_for_model


class CycloneInferenceEngine:
    """
    Coordinates preprocessing, model inference, center localization, 
    classification, confidence scoring, and Grad-CAM generation.
    """
    def __init__(
        self,
        weights_path: Optional[str] = None,
        device: Optional[str] = None,
        confidence_threshold: float = 0.5,
        version: str = "v1.0.0",
    ):
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self.version = version
        self.confidence_threshold = confidence_threshold

        # Initialize model architecture
        self.model = CycloneBaselineCNN(
            in_channels=3,
            num_classes=len(IMD_CYCLONE_CLASSES),
        ).to(self.device)

        self.weights_loaded = False
        if weights_path and os.path.exists(weights_path):
            try:
                state_dict = torch.load(weights_path, map_location=self.device)
                self.model.load_state_dict(state_dict)
                self.weights_loaded = True
            except Exception as e:
                print(f"Warning: Failed to load model weights from {weights_path}: {e}")
        
        self.model.eval()

        # Modular wrappers
        self.detector = CycloneDetector(self.model, threshold=self.confidence_threshold)
        self.classifier = CycloneClassifier(self.model, classes=IMD_CYCLONE_CLASSES)
        self.locator = CycloneCenterLocator(self.model)

    def analyze_image(
        self,
        image_input: Union[bytes, str, Image.Image],
        bbox: Optional[Dict[str, float]] = None,
        include_explainability: bool = True,
        timestamp: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes full pipeline: validation -> preprocessing -> detection -> 
        localization -> classification -> explainability.
        """
        start_time = time.time()
        
        # 1. Image Validation & Loading
        pil_img = validate_and_load_image(image_input, target_channels=3)
        orig_w, orig_h = pil_img.size

        # 2. Tensor Preprocessing
        tensor = preprocess_for_model(pil_img, target_size=(224, 224), channels=3).to(self.device)

        # 3. Cyclone Detection
        detected, det_conf = self.detector.detect(tensor)

        # 4. Center Localization & Geo-mapping
        loc_res = self.locator.locate_center(tensor, orig_width=orig_w, orig_height=orig_h, bbox=bbox)

        # 5. Stage/Intensity Classification
        pred_class, cls_conf, prob_dist = self.classifier.classify(tensor)

        # If not detected, ensure class reflects no cyclone / baseline consistency
        if not detected:
            if "No Cyclone / Non-Depression" in prob_dist:
                pred_class = "No Cyclone / Non-Depression"

        # 6. Explainability (Grad-CAM)
        heatmap_base64 = None
        if include_explainability:
            try:
                cam = GradCAM(self.model)
                heatmap = cam.generate_heatmap(tensor, target_type="detection" if not detected else "classification")
                heatmap_base64 = cam.generate_base64_overlay(pil_img, heatmap, alpha=0.45)
                cam.cleanup()
            except Exception as e:
                print(f"Explainability generation notice: {e}")
                heatmap_base64 = None

        latency_ms = round((time.time() - start_time) * 1000, 2)
        utc_now = timestamp or datetime.now(timezone.utc).isoformat()

        return {
            "timestamp": utc_now,
            "detection": {
                "detected": detected,
                "confidence": det_conf,
                "latitude": loc_res["latitude"],
                "longitude": loc_res["longitude"],
                "pixel_center": loc_res["pixel_center"],
                "normalized_center": loc_res["normalized_center"],
            },
            "classification": {
                "class": pred_class,
                "confidence": cls_conf,
                "probabilities": prob_dist,
            },
            "explainability": {
                "available": heatmap_base64 is not None,
                "heatmap_base64": heatmap_base64,
                "heatmap_path": None,
            },
            "model": {
                "detection_version": self.version,
                "classification_version": self.version,
                "backbone": "CycloneBaselineCNN-v1",
                "weights_loaded": self.weights_loaded,
                "inference_latency_ms": latency_ms,
            },
        }
