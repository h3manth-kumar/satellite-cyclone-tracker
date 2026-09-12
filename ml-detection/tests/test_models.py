"""Tests for ML model architecture, forward pass, and modular wrappers."""

import pytest
import torch
from src.models.baseline_cnn import CycloneBaselineCNN, IMD_CYCLONE_CLASSES
from src.models.detector import CycloneDetector
from src.models.classifier import CycloneClassifier
from src.models.center_locator import CycloneCenterLocator


@pytest.fixture
def dummy_input():
    return torch.randn(2, 3, 224, 224)


@pytest.fixture
def baseline_model():
    model = CycloneBaselineCNN(in_channels=3, num_classes=len(IMD_CYCLONE_CLASSES))
    model.eval()
    return model


def test_baseline_cnn_forward_shapes(baseline_model, dummy_input):
    outputs = baseline_model(dummy_input)

    assert "detection_logit" in outputs
    assert "detection_prob" in outputs
    assert "class_logits" in outputs
    assert "class_probs" in outputs
    assert "center_coords" in outputs

    assert outputs["detection_prob"].shape == (2, 1)
    assert outputs["class_probs"].shape == (2, len(IMD_CYCLONE_CLASSES))
    assert outputs["center_coords"].shape == (2, 2)

    # Probabilities in [0, 1]
    assert (outputs["detection_prob"] >= 0.0).all() and (outputs["detection_prob"] <= 1.0).all()
    # Softmax sums to 1
    sums = outputs["class_probs"].sum(dim=-1)
    assert torch.allclose(sums, torch.ones(2), atol=1e-5)
    # Center coords in [0, 1]
    assert (outputs["center_coords"] >= 0.0).all() and (outputs["center_coords"] <= 1.0).all()


def test_detector_wrapper(baseline_model):
    detector = CycloneDetector(baseline_model, threshold=0.5)
    tensor = torch.randn(1, 3, 224, 224)
    detected, conf = detector.detect(tensor)

    assert isinstance(detected, bool)
    assert isinstance(conf, float)
    assert 0.0 <= conf <= 1.0


def test_classifier_wrapper(baseline_model):
    classifier = CycloneClassifier(baseline_model)
    tensor = torch.randn(1, 3, 224, 224)
    pred_class, conf, prob_dist = classifier.classify(tensor)

    assert pred_class in IMD_CYCLONE_CLASSES
    assert 0.0 <= conf <= 1.0
    assert len(prob_dist) == len(IMD_CYCLONE_CLASSES)
    assert pytest.approx(sum(prob_dist.values()), abs=1e-2) == 1.0


def test_center_locator_wrapper(baseline_model):
    locator = CycloneCenterLocator(baseline_model)
    tensor = torch.randn(1, 3, 224, 224)
    bbox = {"min_lat": 10.0, "max_lat": 20.0, "min_lon": 80.0, "max_lon": 90.0}

    res = locator.locate_center(tensor, orig_width=200, orig_height=200, bbox=bbox)

    assert "pixel_center" in res
    assert "normalized_center" in res
    assert "latitude" in res
    assert "longitude" in res

    assert 0 <= res["pixel_center"]["x"] <= 200
    assert 0 <= res["pixel_center"]["y"] <= 200
    assert 10.0 <= res["latitude"] <= 20.0
    assert 80.0 <= res["longitude"] <= 90.0
