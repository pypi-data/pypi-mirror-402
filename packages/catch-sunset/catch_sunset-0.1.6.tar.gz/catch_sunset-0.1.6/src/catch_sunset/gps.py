"""
GPS coordinate retrieval module.

This module provides functionality to retrieve current GPS coordinates
using various methods with different precision levels.
"""

import urllib.request
import urllib.error
import json
from typing import Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class PrecisionLevel(Enum):
    """GPS coordinate precision levels."""
    HIGH = "high"  # < 10 meters (GPS device, mobile GPS)
    MEDIUM = "medium"  # 10-100 meters (Wi-Fi triangulation)
    LOW = "low"  # 100-5000 meters (Cell tower)
    VERY_LOW = "very_low"  # 5-50 km (IP-based geolocation)
    UNKNOWN = "unknown"  # Unknown precision


@dataclass
class GPSCoordinates:
    """
    GPS coordinates with metadata.

    Attributes:
        latitude: Latitude in decimal degrees (-90 to 90)
        longitude: Longitude in decimal degrees (-180 to 180)
        precision: Estimated precision level
        precision_meters: Approximate precision in meters
        source: Method used to obtain coordinates
    """
    latitude: float
    longitude: float
    precision: PrecisionLevel
    precision_meters: Optional[float]
    source: str

    def __str__(self) -> str:
        """Return human-readable string representation."""
        precision_info = (
            f"±{self.precision_meters}m" if self.precision_meters
            else self.precision.value
        )
        return (
            f"Coordinates: {self.latitude:.6f}°, {self.longitude:.6f}°\n"
            f"Precision: {precision_info}\n"
            f"Source: {self.source}"
        )


def get_coordinates_from_ip() -> Optional[GPSCoordinates]:
    """
    Get approximate GPS coordinates based on IP address.

    This method uses IP-based geolocation which has low precision
    (typically 5-50 km accuracy in urban areas, worse in rural areas).

    Returns:
        GPSCoordinates object if successful, None otherwise.

    Note:
        Requires internet connection. May be blocked by VPNs/proxies.
    """
    try:
        # Using ipapi.co free service (no API key required)
        url = "https://ipapi.co/json/"
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'catch-sunset/0.1.0'}
        )

        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())

        if 'latitude' in data and 'longitude' in data:
            # IP-based geolocation typically has 5-50km precision
            return GPSCoordinates(
                latitude=float(data['latitude']),
                longitude=float(data['longitude']),
                precision=PrecisionLevel.VERY_LOW,
                precision_meters=10000.0,  # Conservative estimate: ~10km
                source=f"IP-based geolocation ({data.get('city', 'Unknown')})"
            )

    except (urllib.error.URLError, json.JSONDecodeError, KeyError, ValueError):
        pass

    return None


def get_coordinates_manual(latitude: float, longitude: float) -> GPSCoordinates:
    """
    Create GPSCoordinates object from manually provided coordinates.

    Args:
        latitude: Latitude in decimal degrees (-90 to 90)
        longitude: Longitude in decimal degrees (-180 to 180)

    Returns:
        GPSCoordinates object with unknown precision.

    Raises:
        ValueError: If coordinates are out of valid range.
    """
    if not -90 <= latitude <= 90:
        raise ValueError(f"Invalid latitude: {latitude}. Must be between -90 and 90.")

    if not -180 <= longitude <= 180:
        raise ValueError(
            f"Invalid longitude: {longitude}. Must be between -180 and 180."
        )

    return GPSCoordinates(
        latitude=latitude,
        longitude=longitude,
        precision=PrecisionLevel.UNKNOWN,
        precision_meters=None,
        source="Manual input"
    )


def get_current_coordinates(
    fallback_to_ip: bool = True
) -> Optional[GPSCoordinates]:
    """
    Get current GPS coordinates using the best available method.

    This function attempts to retrieve coordinates in the following order:
    1. System location services (if implemented in future)
    2. IP-based geolocation (if fallback_to_ip=True)

    Args:
        fallback_to_ip: Whether to fall back to IP-based geolocation.

    Returns:
        GPSCoordinates object if successful, None otherwise.

    Example:
        >>> coords = get_current_coordinates()
        >>> if coords:
        ...     print(f"Location: {coords.latitude}, {coords.longitude}")
        ...     print(f"Precision: ±{coords.precision_meters}m")
    """
    # Future: Add system location services check here
    # For now, we only have IP-based geolocation

    if fallback_to_ip:
        return get_coordinates_from_ip()

    return None


def format_coordinates(coords: GPSCoordinates, format_type: str = "decimal") -> str:
    """
    Format GPS coordinates in different formats.

    Args:
        coords: GPSCoordinates object to format
        format_type: Output format ("decimal", "dms", or "compact")

    Returns:
        Formatted coordinate string.

    Raises:
        ValueError: If format_type is not recognized.
    """
    if format_type == "decimal":
        return f"{coords.latitude:.6f}°, {coords.longitude:.6f}°"

    elif format_type == "dms":
        # Convert to degrees, minutes, seconds
        lat_deg = int(abs(coords.latitude))
        lat_min = int((abs(coords.latitude) - lat_deg) * 60)
        lat_sec = ((abs(coords.latitude) - lat_deg) * 60 - lat_min) * 60
        lat_dir = "N" if coords.latitude >= 0 else "S"

        lon_deg = int(abs(coords.longitude))
        lon_min = int((abs(coords.longitude) - lon_deg) * 60)
        lon_sec = ((abs(coords.longitude) - lon_deg) * 60 - lon_min) * 60
        lon_dir = "E" if coords.longitude >= 0 else "W"

        return (
            f"{lat_deg}°{lat_min}'{lat_sec:.2f}\"{lat_dir}, "
            f"{lon_deg}°{lon_min}'{lon_sec:.2f}\"{lon_dir}"
        )

    elif format_type == "compact":
        return f"{coords.latitude:.6f},{coords.longitude:.6f}"

    else:
        raise ValueError(
            f"Unknown format_type: {format_type}. "
            "Use 'decimal', 'dms', or 'compact'."
        )
