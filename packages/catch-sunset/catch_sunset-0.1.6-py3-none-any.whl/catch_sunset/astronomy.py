"""
Astronomy module for sunset and sunrise calculations.

This module uses Skyfield library to calculate precise sunset and sunrise times,
including azimuth (compass direction) for any location on Earth.
"""
from datetime import date, datetime, timezone, timedelta
from typing import Dict, Any, Tuple
from skyfield import almanac
from skyfield.api import load, Topos, Timescale
from skyfield.jpllib import SpiceKernel


# Cache for ephemeris data to avoid reloading
_ephemeris_cache = None
_timescale_cache = None


def load_ephemeris() -> Tuple[Timescale, SpiceKernel]:
    """
    Load ephemeris data for astronomical calculations.

    This function loads the DE421 ephemeris which contains positions
    of planets and the sun. The data is cached to avoid repeated downloads.

    Returns:
        Tuple containing:
        - Timescale object for time conversions
        - Ephemeris object containing planetary positions

    Raises:
        IOError: If ephemeris data cannot be downloaded or loaded
    """
    global _ephemeris_cache, _timescale_cache

    if _ephemeris_cache is None or _timescale_cache is None:
        loader = load
        _timescale_cache = loader.timescale()
        _ephemeris_cache = loader('de421.bsp')

    return _timescale_cache, _ephemeris_cache


def get_compass_direction(azimuth: float) -> str:
    """
    Convert azimuth angle to compass direction.

    Args:
        azimuth: Angle in degrees (0-360), where:
                 0/360 = North, 90 = East, 180 = South, 270 = West

    Returns:
        Compass direction string (N, NE, E, SE, S, SW, W, NW, NNE, etc.)

    Examples:
        >>> get_compass_direction(0)
        'N'
        >>> get_compass_direction(90)
        'E'
        >>> get_compass_direction(135)
        'SE'
    """
    # Normalize azimuth to 0-360 range
    azimuth = azimuth % 360

    # 16-point compass directions
    directions = [
        "N", "NNE", "NE", "ENE",
        "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW",
        "W", "WNW", "NW", "NNW"
    ]

    # Each direction covers 22.5 degrees (360 / 16)
    index = int((azimuth + 11.25) / 22.5) % 16

    return directions[index]


def calculate_sunset_sunrise(
    latitude: float,
    longitude: float,
    target_date: date
) -> Dict[str, Any]:
    """
    Calculate sunset and sunrise times with directions for a given location and date.

    This function computes the exact times of sunrise and sunset, along with
    the azimuth (compass direction) where the sun will rise/set.

    Args:
        latitude: Latitude in decimal degrees (-90 to 90)
                 Positive = North, Negative = South
        longitude: Longitude in decimal degrees (-180 to 180)
                  Positive = East, Negative = West
        target_date: Date for which to calculate sunset/sunrise

    Returns:
        Dictionary containing:
        {
            'sunrise': {
                'sunrise_time': datetime object (timezone-aware),
                'sunrise_azimuth': float (degrees, 0-360),
                'sunrise_direction': str (compass direction)
            },
            'sunset': {
                'sunset_time': datetime object (timezone-aware),
                'sunset_azimuth': float (degrees, 0-360),
                'sunset_direction': str (compass direction)
            }
        }

    Raises:
        ValueError: If latitude or longitude are out of valid ranges
        RuntimeError: If sunset/sunrise cannot be calculated (e.g., polar night/day)

    Examples:
        >>> result = calculate_sunset_sunrise(51.5074, -0.1278, date(2025, 1, 15))
        >>> print(result['sunrise']['sunrise_direction'])
        'SE'
    """
    # Validate inputs
    if not -90 <= latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90 degrees")

    if not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180 degrees")

    # Load ephemeris data
    ts, eph = load_ephemeris()

    # Create location (Topos for almanac, full location for observations)
    topos = Topos(
        latitude_degrees=latitude,
        longitude_degrees=longitude
    )
    location = eph['earth'] + topos

    # Define the time range for the target date (full 24 hours)
    t0 = ts.utc(target_date.year, target_date.month, target_date.day, 0, 0, 0)
    t1 = ts.utc(target_date.year, target_date.month, target_date.day, 23, 59, 59)

    # Find sunrise and sunset times
    times, events = almanac.find_discrete(t0, t1, almanac.sunrise_sunset(eph, topos))

    # Parse results
    sunrise_time = None
    sunset_time = None

    for time, event in zip(times, events):
        if event == 1:  # Sunrise
            sunrise_time = time
        elif event == 0:  # Sunset
            sunset_time = time

    # Handle cases where sun doesn't rise or set (polar regions)
    if sunrise_time is None or sunset_time is None:
        # Check if it's polar day (sun never sets) or polar night (sun never rises)
        # Sample the sun's altitude at noon
        noon = ts.utc(target_date.year, target_date.month, target_date.day, 12, 0, 0)
        sun = eph['sun']
        astrometric = location.at(noon).observe(sun)
        alt, az, distance = astrometric.apparent().altaz()

        if alt.degrees > 0:
            # Polar day (sun doesn't set)
            # Use noon and midnight as approximations
            sunrise_time = ts.utc(target_date.year, target_date.month, target_date.day, 0, 0, 0)
            sunset_time = ts.utc(target_date.year, target_date.month, target_date.day, 23, 59, 59)
        else:
            # Polar night (sun doesn't rise)
            raise RuntimeError(
                f"Sun does not rise on {target_date} at latitude {latitude}. "
                "This location is experiencing polar night."
            )

    # Calculate azimuth for sunrise
    sun = eph['sun']
    sunrise_astrometric = location.at(sunrise_time).observe(sun)
    sunrise_alt, sunrise_az, _ = sunrise_astrometric.apparent().altaz()

    # Calculate azimuth for sunset
    sunset_astrometric = location.at(sunset_time).observe(sun)
    sunset_alt, sunset_az, _ = sunset_astrometric.apparent().altaz()

    # Convert skyfield times to Python datetime objects
    sunrise_dt = sunrise_time.utc_datetime()
    sunset_dt = sunset_time.utc_datetime()

    # Build result dictionary
    result = {
        'sunrise': {
            'sunrise_time': sunrise_dt,
            'sunrise_azimuth': sunrise_az.degrees,
            'sunrise_direction': get_compass_direction(sunrise_az.degrees)
        },
        'sunset': {
            'sunset_time': sunset_dt,
            'sunset_azimuth': sunset_az.degrees,
            'sunset_direction': get_compass_direction(sunset_az.degrees)
        }
    }

    return result
