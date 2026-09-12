"""Model Evaluation and Metrics Computation Pipeline."""

import os
from typing import Dict, Any, Optional
import numpy as np
import torch
from torch.utils.data import DataLoader
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    accuracy_score,
    confusion_matrix,
    classification_report,
)

from src.models.baseline_cnn import CycloneBaselineCNN, IMD_CYCLONE_CLASSES
from src.training.dataset import CycloneDataset


def evaluate_model(
    model: CycloneBaselineCNN,
    val_loader: DataLoader,
    device: torch.device,
) -> Dict[str, Any]:
    """
    Computes comprehensive detection, classification, and localization metrics.
    """
    model.eval()
    y_det_true = []
    y_det_pred = []
    y_cls_true = []
    y_cls_pred = []
    loc_errors = []

    with torch.no_grad():
        for batch in val_loader:
            images = batch["image"].to(device)
            det_targets = batch["detection_label"].cpu().numpy()
            cls_targets = batch["class_label"].cpu().numpy()
            loc_targets = batch["center_label"].cpu().numpy()

            outputs = model(images)
            det_probs = outputs["detection_prob"].cpu().numpy().flatten()
            cls_preds = outputs["class_probs"].cpu().numpy().argmax(axis=-1)
            loc_preds = outputs["center_coords"].cpu().numpy()

            det_binary = (det_probs >= 0.5).astype(int)

            y_det_true.extend(det_targets.astype(int))
            y_det_pred.extend(det_binary)
            y_cls_true.extend(cls_targets)
            y_cls_pred.extend(cls_preds)

            # Euclidean error in normalized coordinate space
            for i in range(len(loc_targets)):
                if det_targets[i] == 1.0:
                    err = np.linalg.norm(loc_preds[i] - loc_targets[i])
                    loc_errors.append(err)

    # Detection Metrics
    det_precision = precision_score(y_det_true, y_det_pred, zero_division=0)
    det_recall = recall_score(y_det_true, y_det_pred, zero_division=0)
    det_f1 = f1_score(y_det_true, y_det_pred, zero_division=0)

    # Classification Metrics
    cls_acc = accuracy_score(y_cls_true, y_cls_pred)
    cls_macro_f1 = f1_score(y_cls_true, y_cls_pred, average="macro", zero_division=0)
    cm = confusion_matrix(y_cls_true, y_cls_pred, labels=list(range(len(IMD_CYCLONE_CLASSES))))

    mean_loc_error = float(np.mean(loc_errors)) if loc_errors else 0.0

    return {
        "detection": {
            "precision": round(float(det_precision), 4),
            "recall": round(float(det_recall), 4),
            "f1_score": round(float(det_f1), 4),
        },
        "classification": {
            "accuracy": round(float(cls_acc), 4),
            "macro_f1": round(float(cls_macro_f1), 4),
            "confusion_matrix": cm.tolist(),
        },
        "localization": {
            "mean_normalized_error": round(mean_loc_error, 4),
            "samples_evaluated": len(loc_errors),
        },
    }


if __name__ == "__main__":
    import json
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = CycloneBaselineCNN(num_classes=len(IMD_CYCLONE_CLASSES)).to(dev)
    ckpt_path = "artifacts/models/cyclone_baseline_v1.pth"
    if os.path.exists(ckpt_path):
        model.load_state_dict(torch.load(ckpt_path, map_location=dev))
        print(f"Loaded checkpoint from: {ckpt_path}")
    val_set = CycloneDataset(num_samples=50, is_training=False)
    val_ld = DataLoader(val_set, batch_size=16, shuffle=False)
    metrics = evaluate_model(model, val_ld, dev)
    print("Evaluation Results:")
    print(json.dumps(metrics, indent=2))
