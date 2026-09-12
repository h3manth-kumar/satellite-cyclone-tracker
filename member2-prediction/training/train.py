"""
Training script for CycloneAI ML Prediction Model (Member 2).
Enforces cyclone/event-based train/val/test splits to avoid temporal/storm data leakage.
"""

from pathlib import Path
import sys

# Ensure package root is in python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
import logging
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from data.cleaner import clean_cyclone_dataframe, regularize_synoptic_intervals
from data.features import extract_kinematic_features
from data.dataset import CycloneTrackDataset, split_cyclones_by_event
from models.recurrent_track_model import CycloneTrackGRU
from models.model_registry import save_checkpoint, DEFAULT_MODEL_FILE

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Trainer")


def train_model(
    data_csv_path: Path,
    output_checkpoint: Path = DEFAULT_MODEL_FILE,
    epochs: int = 50,
    batch_size: int = 16,
    lr: float = 1e-3,
    hidden_dim: int = 64,
    device: str = None,
) -> float:
    """
    Executes end-to-end model training.
    """
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    logger.info(f"Loading dataset from: {data_csv_path}")
    raw_df = pd.read_csv(data_csv_path)

    logger.info("Cleaning raw cyclone dataset...")
    cleaned_df = clean_cyclone_dataframe(raw_df)

    logger.info("Regularizing tracks to 6-hour synoptic intervals...")
    regularized_df = regularize_synoptic_intervals(cleaned_df, freq_hours=6)

    logger.info("Engineering kinematic, spatial, and intensity features...")
    feat_df = extract_kinematic_features(regularized_df)

    logger.info("Splitting dataset by cyclone/event to prevent data leakage...")
    train_df, val_df, test_df = split_cyclones_by_event(feat_df, random_state=42)
    logger.info(
        f"Storm split counts: Train={train_df['cyclone_id'].nunique()}, "
        f"Val={val_df['cyclone_id'].nunique()}, Test={test_df['cyclone_id'].nunique()}"
    )

    # Instantiate datasets
    train_ds = CycloneTrackDataset(train_df, fit_scaler=True)
    scaler = train_ds.scaler
    val_ds = CycloneTrackDataset(val_df, scaler=scaler)

    if len(train_ds) == 0:
        raise ValueError(
            "Training dataset has 0 sequences. Please check sequence lengths and lookback."
        )

    # In case val dataset is small, combine or evaluate
    if len(val_ds) == 0:
        logger.warning("Validation partition empty due to small storm catalog; evaluating on train subset.")
        val_ds = train_ds

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

    model = CycloneTrackGRU(
        input_dim=12,
        hidden_dim=hidden_dim,
        num_layers=2,
        num_horizons=4,
        dropout=0.20,
    ).to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    loss_fn = nn.SmoothL1Loss(reduction="none")

    best_val_loss = float("inf")

    logger.info(f"Starting training for {epochs} epochs on device: {device}")

    for epoch in range(1, epochs + 1):
        model.train()
        train_losses = []

        for batch in train_loader:
            x = batch["x"].to(device)
            track_disp = batch["track_disp"].to(device)  # [B, 4, 2]
            intensity_disp = batch["intensity_disp"].to(device)  # [B, 4, 2]
            mask = batch["mask"].to(device)  # [B, 4]
            intensity_mask = batch.get("intensity_mask", mask).to(device)  # [B, 4]

            optimizer.zero_grad()
            outputs = model(x)

            # Compute masked loss for track displacements
            track_loss_all = loss_fn(outputs["track_disp"], track_disp)  # [B, 4, 2]
            masked_track_loss = (track_loss_all.mean(dim=-1) * mask).sum() / mask.sum().clamp(min=1.0)

            # Compute masked loss for intensity changes strictly where valid labels exist
            intensity_loss_all = loss_fn(outputs["intensity_disp"], intensity_disp)  # [B, 4, 2]
            int_sum = intensity_mask.sum()
            if int_sum > 0:
                masked_intensity_loss = (intensity_loss_all.mean(dim=-1) * intensity_mask).sum() / int_sum
            else:
                masked_intensity_loss = torch.tensor(0.0, device=device)

            total_loss = masked_track_loss + 0.10 * masked_intensity_loss

            total_loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

            train_losses.append(total_loss.item())

        # Validation
        model.eval()
        val_losses = []
        with torch.no_grad():
            for batch in val_loader:
                x = batch["x"].to(device)
                track_disp = batch["track_disp"].to(device)
                mask = batch["mask"].to(device)

                outputs = model(x)
                track_loss_all = loss_fn(outputs["track_disp"], track_disp)
                v_loss = (track_loss_all.mean(dim=-1) * mask).sum() / mask.sum().clamp(min=1.0)
                val_losses.append(v_loss.item())

        avg_train = np.mean(train_losses)
        avg_val = np.mean(val_losses)

        if epoch % 10 == 0 or epoch == epochs:
            logger.info(f"Epoch {epoch:02d}/{epochs} - Train Loss: {avg_train:.4f} - Val Loss: {avg_val:.4f}")

        if avg_val < best_val_loss:
            best_val_loss = avg_val
            save_checkpoint(
                model,
                scaler,
                filepath=output_checkpoint,
                metadata={"best_val_loss": float(best_val_loss), "epoch": epoch},
            )

    logger.info(f"Training completed. Best validation loss: {best_val_loss:.4f}")
    return float(best_val_loss)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train CycloneAI prediction model")
    parser.add_argument(
        "--data",
        type=str,
        default=str(Path(__file__).resolve().parent.parent / "data" / "benchmark_sample.csv"),
        help="Path to training CSV file",
    )
    parser.add_argument(
        "--epochs", type=int, default=40, help="Number of training epochs"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(DEFAULT_MODEL_FILE),
        help="Target checkpoint file path",
    )
    args = parser.parse_args()

    train_model(Path(args.data), Path(args.output), epochs=args.epochs)
