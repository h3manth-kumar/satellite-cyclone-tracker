"""
Unit tests for sliding-window sequence generation and event-based partitioning.
"""

from pathlib import Path
import pytest
import pandas as pd
from data.cleaner import clean_cyclone_dataframe, regularize_synoptic_intervals
from data.features import extract_kinematic_features
from data.dataset import CycloneTrackDataset, split_cyclones_by_event

SAMPLE_PATH = Path(__file__).resolve().parent.parent / "data" / "benchmark_sample.csv"


def test_split_cyclones_by_event_disjoint():
    raw_df = pd.read_csv(SAMPLE_PATH)
    cleaned = clean_cyclone_dataframe(raw_df)
    feat_df = extract_kinematic_features(cleaned)

    train_df, val_df, test_df = split_cyclones_by_event(feat_df, random_state=42)

    train_cids = set(train_df["cyclone_id"].unique())
    val_cids = set(val_df["cyclone_id"].unique())
    test_cids = set(test_df["cyclone_id"].unique())

    # Strict disjointness (Zero leakage)
    assert len(train_cids.intersection(val_cids)) == 0
    assert len(train_cids.intersection(test_cids)) == 0
    assert len(val_cids.intersection(test_cids)) == 0


def test_cyclone_track_dataset_shapes():
    raw_df = pd.read_csv(SAMPLE_PATH)
    cleaned = clean_cyclone_dataframe(raw_df)
    reg_df = regularize_synoptic_intervals(cleaned)
    feat_df = extract_kinematic_features(reg_df)

    dataset = CycloneTrackDataset(feat_df, fit_scaler=True, lookback_steps=4)
    assert len(dataset) > 0

    sample = dataset[0]
    assert sample["x"].shape == (4, 12)
    assert sample["curr_state"].shape == (4,)
    assert sample["track_disp"].shape == (4, 2)
    assert sample["intensity_disp"].shape == (4, 2)
    assert sample["abs_track"].shape == (4, 2)
    assert sample["mask"].shape == (4,)
