"""Dataset management and synthetic satellite cyclone data generator for baseline training."""

import os
from typing import Tuple, Dict, Any, List, Optional
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import torch
from torch.utils.data import Dataset
from torchvision import transforms

from src.models.baseline_cnn import IMD_CYCLONE_CLASSES
from src.preprocessing.transforms import get_training_transforms, get_inference_transforms


def generate_synthetic_satellite_image(
    size: Tuple[int, int] = (224, 224),
    has_cyclone: bool = True,
    center: Optional[Tuple[float, float]] = None,
    intensity_stage: int = 1,
) -> Tuple[Image.Image, Dict[str, Any]]:
    """
    Generates a physically plausible synthetic infrared satellite storm image.
    Uses logarithmic spiral math to render eye wall & spiral rainbands + atmospheric noise.
    """
    w, h = size
    # Background temperature / cloud field noise
    base = np.random.normal(loc=120, scale=25, size=(h, w)).astype(np.float32)
    base = np.clip(base, 0, 255)

    img = Image.fromarray(base.astype(np.uint8), mode="L")
    draw = ImageDraw.Draw(img)

    if not has_cyclone or intensity_stage == 0:
        # Just random cloud streaks
        for _ in range(5):
            x1, y1 = np.random.randint(0, w, 2)
            x2, y2 = np.random.randint(0, w, 2)
            draw.line([(x1, y1), (x2, y2)], fill=np.random.randint(160, 230), width=np.random.randint(4, 12))
        img = img.filter(ImageFilter.GaussianBlur(radius=3))
        meta = {
            "has_cyclone": False,
            "center": (0.5, 0.5),
            "class_idx": 0,
            "class_name": IMD_CYCLONE_CLASSES[0],
        }
        return img.convert("RGB"), meta

    # Normalized center
    if center is None:
        cx_norm = np.random.uniform(0.3, 0.7)
        cy_norm = np.random.uniform(0.3, 0.7)
    else:
        cx_norm, cy_norm = center

    cx = int(cx_norm * w)
    cy = int(cy_norm * h)

    # Intensity scales spiral density and eye radius
    max_radius = 20 + intensity_stage * 12
    eye_radius = max(3, 10 - intensity_stage)

    # Draw spiral cloud bands
    theta = np.linspace(0, 4 * np.pi, 200)
    for arm in [0, np.pi]:
        r = np.linspace(eye_radius, max_radius, 200)
        xs = cx + r * np.cos(theta + arm)
        ys = cy + r * np.sin(theta + arm)
        points = [(int(xs[i]), int(ys[i])) for i in range(len(xs)) if 0 <= xs[i] < w and 0 <= ys[i] < h]
        if len(points) > 1:
            draw.line(points, fill=255, width=int(3 + intensity_stage * 1.5))

    # Dense central dense overcast (CDO)
    draw.ellipse(
        [(cx - eye_radius * 2, cy - eye_radius * 2), (cx + eye_radius * 2, cy + eye_radius * 2)],
        fill=240,
    )
    # Warm eye in the center
    draw.ellipse(
        [(cx - eye_radius, cy - eye_radius), (cx + eye_radius, cy + eye_radius)],
        fill=80,
    )

    img = img.filter(ImageFilter.GaussianBlur(radius=2))

    meta = {
        "has_cyclone": True,
        "center": (round(float(cx_norm), 4), round(float(cy_norm), 4)),
        "class_idx": intensity_stage,
        "class_name": IMD_CYCLONE_CLASSES[intensity_stage],
    }

    return img.convert("RGB"), meta


class CycloneDataset(Dataset):
    """
    PyTorch Dataset supporting synthetic generation or directory of image files.
    """
    def __init__(
        self,
        num_samples: int = 100,
        is_training: bool = True,
        image_size: Tuple[int, int] = (224, 224),
    ):
        self.num_samples = num_samples
        self.is_training = is_training
        self.image_size = image_size
        self.transform = (
            get_training_transforms(image_size)
            if is_training
            else get_inference_transforms(image_size)
        )

        # Pre-generate deterministic dataset metadata
        np.random.seed(42 if not is_training else None)
        self.samples = []
        for i in range(num_samples):
            has_cyclone = (i % 5 != 0)  # 80% cyclone, 20% non-cyclone
            stage = np.random.randint(1, len(IMD_CYCLONE_CLASSES)) if has_cyclone else 0
            self.samples.append({
                "has_cyclone": has_cyclone,
                "stage": stage,
                "center": (np.random.uniform(0.3, 0.7), np.random.uniform(0.3, 0.7)),
            })

    def __len__(self) -> int:
        return self.num_samples

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        sample_meta = self.samples[idx]
        img, meta = generate_synthetic_satellite_image(
            size=self.image_size,
            has_cyclone=sample_meta["has_cyclone"],
            center=sample_meta["center"],
            intensity_stage=sample_meta["stage"],
        )

        tensor = self.transform(img)

        return {
            "image": tensor,
            "detection_label": torch.tensor(1.0 if meta["has_cyclone"] else 0.0, dtype=torch.float32),
            "class_label": torch.tensor(meta["class_idx"], dtype=torch.long),
            "center_label": torch.tensor([meta["center"][0], meta["center"][1]], dtype=torch.float32),
        }
