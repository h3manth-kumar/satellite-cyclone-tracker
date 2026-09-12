"""Image transformation, preprocessing, and tensor preparation."""

from typing import Tuple, Union
import numpy as np
from PIL import Image
import torch
from torchvision import transforms


DEFAULT_IMAGE_SIZE = (224, 224)
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def get_inference_transforms(
    target_size: Tuple[int, int] = DEFAULT_IMAGE_SIZE,
    channels: int = 3,
) -> transforms.Compose:
    """Returns torchvision composition for inference preprocessing."""
    transform_list = [
        transforms.Resize(target_size),
        transforms.ToTensor(),
    ]
    if channels == 3:
        transform_list.append(transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD))
    elif channels == 1:
        transform_list.append(transforms.Normalize(mean=[0.5], std=[0.5]))
    
    return transforms.Compose(transform_list)


def get_training_transforms(
    target_size: Tuple[int, int] = DEFAULT_IMAGE_SIZE,
    channels: int = 3,
) -> transforms.Compose:
    """Returns robust data augmentation pipeline for cyclone training."""
    transform_list = [
        transforms.Resize(target_size),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomVerticalFlip(p=0.5),
        transforms.RandomRotation(degrees=180),  # Cyclonic patterns are rotational
        transforms.ColorJitter(brightness=0.1, contrast=0.1),
        transforms.ToTensor(),
    ]
    if channels == 3:
        transform_list.append(transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD))
    elif channels == 1:
        transform_list.append(transforms.Normalize(mean=[0.5], std=[0.5]))
        
    return transforms.Compose(transform_list)


def preprocess_for_model(
    image: Image.Image,
    target_size: Tuple[int, int] = DEFAULT_IMAGE_SIZE,
    channels: int = 3,
) -> torch.Tensor:
    """
    Transforms PIL image into batched PyTorch tensor [1, C, H, W].
    """
    transform = get_inference_transforms(target_size=target_size, channels=channels)
    tensor = transform(image)
    return tensor.unsqueeze(0)  # Add batch dimension [1, C, H, W]
