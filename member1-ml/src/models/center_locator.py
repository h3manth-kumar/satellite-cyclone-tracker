"""Cyclone Center Localization Component."""

from typing import Tuple, Dict, Any, Optional
import torch
from src.models.baseline_cnn import CycloneBaselineCNN
from src.preprocessing.geo_utils import pixel_to_latlon, validate_coordinates


class CycloneCenterLocator:
    """High-level center localization interface."""
    def __init__(self, model: CycloneBaselineCNN):
        self.model = model

    def locate_center(
        self,
        tensor: torch.Tensor,
        orig_width: int,
        orig_height: int,
        bbox: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Locates the normalized center coordinates and maps to geographical coords if bbox exists.
        
        Returns:
            Dict containing:
              - 'pixel_center': {'x': int, 'y': int}
              - 'normalized_center': {'x': float, 'y': float}
              - 'latitude': float or None
              - 'longitude': float or None
        """
        self.model.eval()
        with torch.no_grad():
            outputs = self.model(tensor)
            coords = outputs["center_coords"][0].cpu().numpy()
            
            norm_x = float(coords[0])
            norm_y = float(coords[1])

            pixel_x = int(round(norm_x * orig_width))
            pixel_y = int(round(norm_y * orig_height))

            # Geo mapping
            lat, lon = pixel_to_latlon(
                pixel_x=pixel_x,
                pixel_y=pixel_y,
                image_width=orig_width,
                image_height=orig_height,
                bbox=bbox,
            )

            return {
                "pixel_center": {"x": pixel_x, "y": pixel_y},
                "normalized_center": {"x": round(norm_x, 4), "y": round(norm_y, 4)},
                "latitude": lat,
                "longitude": lon,
            }
