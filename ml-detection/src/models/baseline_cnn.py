"""Unified Multi-Task Baseline Architecture for Cyclone Detection, Classification & Localization."""

from typing import Dict, Any, List, Optional
import torch
import torch.nn as nn
import torch.nn.functional as F


# Standard verified IMD Cyclone Classification Categories
IMD_CYCLONE_CLASSES = [
    "No Cyclone / Non-Depression",
    "Depression",
    "Deep Depression",
    "Cyclonic Storm",
    "Severe Cyclonic Storm",
    "Very Severe Cyclonic Storm",
    "Extremely Severe Cyclonic Storm",
    "Super Cyclonic Storm",
]


class ConvBlock(nn.Module):
    """Standard Conv-BatchNorm-ReLU block with residual shortcut."""
    def __init__(self, in_channels: int, out_channels: int, stride: int = 1):
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=stride, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, stride=1, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(out_channels)

        self.shortcut = nn.Sequential()
        if stride != 1 or in_channels != out_channels:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(out_channels),
            )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        residual = self.shortcut(x)
        out = self.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out += residual
        return self.relu(out)


class CycloneBaselineCNN(nn.Module):
    """
    Multi-task convolutional neural network for tropical cyclone analysis.
    
    Shares a deep convolutional feature extractor, branching into:
      1. Detection Head (Binary: Cyclone present vs absent)
      2. Classification Head (Multi-class: IMD intensity stages)
      3. Localization Head (Continuous: Normalized Center [x, y] in [0, 1])
    """
    def __init__(
        self,
        in_channels: int = 3,
        num_classes: int = len(IMD_CYCLONE_CLASSES),
        feature_dim: int = 256,
    ):
        super().__init__()
        self.in_channels = in_channels
        self.num_classes = num_classes

        # Initial stem
        self.stem = nn.Sequential(
            nn.Conv2d(in_channels, 32, kernel_size=7, stride=2, padding=3, bias=False),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=3, stride=2, padding=1),
        )

        # Feature Backbone stages
        self.stage1 = ConvBlock(32, 64, stride=1)
        self.stage2 = ConvBlock(64, 128, stride=2)
        self.stage3 = ConvBlock(128, 256, stride=2)
        self.stage4 = ConvBlock(256, feature_dim, stride=2)

        # Global average pool
        self.gap = nn.AdaptiveAvgPool2d((1, 1))

        # 1. Detection Head: outputs single logit for cyclone presence
        self.detection_head = nn.Sequential(
            nn.Linear(feature_dim, 64),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(64, 1),
        )

        # 2. Classification Head: outputs logits for IMD intensity stages
        self.classification_head = nn.Sequential(
            nn.Linear(feature_dim, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(128, num_classes),
        )

        # 3. Center Localization Head: outputs [center_x, center_y] in range [0, 1]
        self.localization_head = nn.Sequential(
            nn.Linear(feature_dim, 64),
            nn.ReLU(inplace=True),
            nn.Linear(64, 2),
            nn.Sigmoid(),  # Bound normalized coords to [0, 1]
        )

    def get_last_conv_layer(self) -> nn.Module:
        """Returns target convolutional layer for Grad-CAM explainability."""
        return self.stage4.conv2

    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Forward pass.
        Returns dictionary of tensors:
          - 'detection_logit': [B, 1]
          - 'detection_prob': [B, 1] in [0, 1]
          - 'class_logits': [B, num_classes]
          - 'class_probs': [B, num_classes] summing to 1
          - 'center_coords': [B, 2] in [0, 1]
        """
        x = self.stem(x)
        x = self.stage1(x)
        x = self.stage2(x)
        x = self.stage3(x)
        features = self.stage4(x)

        pooled = self.gap(features).flatten(1)

        # Detection
        det_logit = self.detection_head(pooled)
        det_prob = torch.sigmoid(det_logit)

        # Classification
        cls_logits = self.classification_head(pooled)
        cls_probs = F.softmax(cls_logits, dim=-1)

        # Localization
        center_coords = self.localization_head(pooled)

        return {
            "features": features,
            "detection_logit": det_logit,
            "detection_prob": det_prob,
            "class_logits": cls_logits,
            "class_probs": cls_probs,
            "center_coords": center_coords,
        }
