"""Geographical coordinate calculation and validation utilities."""

from typing import Tuple, Optional, Dict, Any


def validate_coordinates(latitude: float, longitude: float) -> bool:
    """Checks whether lat and lon fall within valid Earth coordinate ranges."""
    if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
        return False
    if latitude < -90.0 or latitude > 90.0:
        return False
    if longitude < -180.0 or longitude > 180.0:
        return False
    return True


def pixel_to_latlon(
    pixel_x: float,
    pixel_y: float,
    image_width: int,
    image_height: int,
    bbox: Optional[Dict[str, float]] = None,
) -> Tuple[Optional[float], Optional[float]]:
    """
    Converts pixel (or normalized) coordinates into Latitude and Longitude.

    bbox format expected:
    {
        "min_lat": float,
        "max_lat": float,
        "min_lon": float,
        "max_lon": float
    }
    
    If bbox is None or incomplete, returns (None, None).
    """
    if bbox is None:
        return None, None

    required_keys = {"min_lat", "max_lat", "min_lon", "max_lon"}
    if not required_keys.issubset(bbox.keys()):
        return None, None

    min_lat = bbox["min_lat"]
    max_lat = bbox["max_lat"]
    min_lon = bbox["min_lon"]
    max_lon = bbox["max_lon"]

    if not (validate_coordinates(min_lat, min_lon) and validate_coordinates(max_lat, max_lon)):
        return None, None

    # Fraction along width and height
    norm_x = pixel_x / float(image_width)
    norm_y = pixel_y / float(image_height)

    # Note: Satellite image Y=0 is typically top (North / max_lat), Y=H is bottom (South / min_lat)
    lon = min_lon + norm_x * (max_lon - min_lon)
    lat = max_lat - norm_y * (max_lat - min_lat)

    lon = round(float(lon), 4)
    lat = round(float(lat), 4)

    return lat, lon


def latlon_to_pixel(
    latitude: float,
    longitude: float,
    image_width: int,
    image_height: int,
    bbox: Dict[str, float],
) -> Tuple[Optional[int], Optional[int]]:
    """
    Converts Latitude and Longitude into image pixel coordinates (X, Y).
    """
    if not validate_coordinates(latitude, longitude):
        return None, None

    min_lat = bbox.get("min_lat")
    max_lat = bbox.get("max_lat")
    min_lon = bbox.get("min_lon")
    max_lon = bbox.get("max_lon")

    if None in (min_lat, max_lat, min_lon, max_lon):
        return None, None

    if max_lon == min_lon or max_lat == min_lat:
        return None, None

    norm_x = (longitude - min_lon) / (max_lon - min_lon)
    norm_y = (max_lat - latitude) / (max_lat - min_lat)

    pixel_x = int(round(norm_x * image_width))
    pixel_y = int(round(norm_y * image_height))

    return pixel_x, pixel_y
