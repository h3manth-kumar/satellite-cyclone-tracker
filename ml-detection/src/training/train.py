"""Baseline Model Training Pipeline for Cyclone Detection, Classification & Localization."""

import os
import argparse
from typing import Dict, Any, Optional
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from src.models.baseline_cnn import CycloneBaselineCNN, IMD_CYCLONE_CLASSES
from src.training.dataset import CycloneDataset


def train_baseline_model(
    epochs: int = 5,
    batch_size: int = 16,
    learning_rate: float = 1e-3,
    num_train_samples: int = 200,
    num_val_samples: int = 50,
    output_dir: str = "artifacts/models",
    device: Optional[str] = None,
) -> str:
    """
    Trains baseline Cyclone CNN model with multi-task loss.
    """
    os.makedirs(output_dir, exist_ok=True)
    dev = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
    print(f"Training on device: {dev}")

    train_dataset = CycloneDataset(num_samples=num_train_samples, is_training=True)
    val_dataset = CycloneDataset(num_samples=num_val_samples, is_training=False)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    model = CycloneBaselineCNN(in_channels=3, num_classes=len(IMD_CYCLONE_CLASSES)).to(dev)

    criterion_det = nn.BCEWithLogitsLoss()
    criterion_cls = nn.CrossEntropyLoss()
    criterion_loc = nn.MSELoss()

    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-4)

    best_val_loss = float("inf")
    save_path = os.path.join(output_dir, "cyclone_baseline_v1.pth")

    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0

        for batch in train_loader:
            images = batch["image"].to(dev)
            det_targets = batch["detection_label"].unsqueeze(1).to(dev)
            cls_targets = batch["class_label"].to(dev)
            loc_targets = batch["center_label"].to(dev)

            optimizer.zero_grad()
            outputs = model(images)

            loss_det = criterion_det(outputs["detection_logit"], det_targets)
            loss_cls = criterion_cls(outputs["class_logits"], cls_targets)
            loss_loc = criterion_loc(outputs["center_coords"], loc_targets)

            # Combined multi-task loss
            total_loss = loss_det + loss_cls + 2.0 * loss_loc
            total_loss.backward()
            optimizer.step()

            train_loss += total_loss.item() * images.size(0)

        train_loss /= len(train_dataset)

        # Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for batch in val_loader:
                images = batch["image"].to(dev)
                det_targets = batch["detection_label"].unsqueeze(1).to(dev)
                cls_targets = batch["class_label"].to(dev)
                loc_targets = batch["center_label"].to(dev)

                outputs = model(images)
                loss_det = criterion_det(outputs["detection_logit"], det_targets)
                loss_cls = criterion_cls(outputs["class_logits"], cls_targets)
                loss_loc = criterion_loc(outputs["center_coords"], loc_targets)

                total_loss = loss_det + loss_cls + 2.0 * loss_loc
                val_loss += total_loss.item() * images.size(0)

        val_loss /= len(val_dataset)

        print(f"Epoch [{epoch}/{epochs}] - Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), save_path)
            print(f"  --> Saved best checkpoint to {save_path}")

    print(f"Training complete. Best model weights at: {save_path}")
    return save_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Cyclone Baseline CNN")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--train-samples", type=int, default=100)
    parser.add_argument("--val-samples", type=int, default=20)
    parser.add_argument("--output-dir", type=str, default="artifacts/models")
    args = parser.parse_args()

    train_baseline_model(
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        num_train_samples=args.train_samples,
        num_val_samples=args.val_samples,
        output_dir=args.output_dir,
    )
