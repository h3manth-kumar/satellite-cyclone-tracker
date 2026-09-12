"""Tests for Grad-CAM explainability generation."""

import numpy as np
import torch
from PIL import Image
from src.models.baseline_cnn import CycloneBaselineCNN
from src.explainability.gradcam import GradCAM


def test_gradcam_heatmap_generation():
    model = CycloneBaselineCNN()
    cam = GradCAM(model)

    dummy_tensor = torch.randn(1, 3, 224, 224)
    heatmap = cam.generate_heatmap(dummy_tensor, target_class_idx=1)

    assert isinstance(heatmap, np.ndarray)
    assert heatmap.shape == (224, 224)
    assert not np.isnan(heatmap).any()
    assert not np.isinf(heatmap).any()
    assert (heatmap >= 0.0).all() and (heatmap <= 1.0).all()

    cam.cleanup()


def test_gradcam_overlay_and_base64():
    model = CycloneBaselineCNN()
    cam = GradCAM(model)

    dummy_tensor = torch.randn(1, 3, 224, 224)
    heatmap = cam.generate_heatmap(dummy_tensor)

    pil_img = Image.new("RGB", (224, 224), color=(100, 150, 200))
    overlay = cam.overlay_heatmap(pil_img, heatmap)

    assert isinstance(overlay, Image.Image)
    assert overlay.size == (224, 224)

    b64 = cam.generate_base64_overlay(pil_img, heatmap)
    assert isinstance(b64, str)
    assert b64.startswith("data:image/png;base64,")
    assert len(b64) > 100

    cam.cleanup()
