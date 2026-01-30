"""
Moon module for moon phase and moonrise/moonset calculations.

This module uses Skyfield library to calculate moon phases, illumination,
and precise moonrise/moonset times with directions.
"""
from datetime import date, datetime, timedelta
from typing import Dict, Any, Optional
from skyfield import almanac
from skyfield.api import Topos
from catch_sunset.astronomy import load_ephemeris, get_compass_direction


def calculate_moon_phase(target_date: date) -> Dict[str, Any]:
    """
    Calculate moon phase and illumination for a given date.

    Args:
        target_date: Date for which to calculate moon phase

    Returns:
        Dictionary containing:
        {
            'illumination': float (0-100, percentage of moon illuminated),
            'phase_name': str (e.g., 'New Moon', 'Full Moon', 'Waxing Crescent'),
            'is_full_moon_period': bool (True if within ±3 days of full moon)
        }

    Examples:
        >>> result = calculate_moon_phase(date(2025, 1, 13))
        >>> print(result['phase_name'])
        'Full Moon'
        >>> print(result['illumination'])
        99.8
    """
    ts, eph = load_ephemeris()

    # Create time object for the target date at noon UTC
    t = ts.utc(target_date.year, target_date.month, target_date.day, 12, 0, 0)

    # Calculate moon illumination using Skyfield's built-in method
    earth = eph['earth']
    moon = eph['moon']
    sun = eph['sun']

    # Calculate phase fraction (0.0 = new moon, 1.0 = full moon)
    e = earth.at(t)
    m = e.observe(moon)

    # fraction_illuminated() returns a value between 0 and 1
    phase_fraction = m.fraction_illuminated(sun)

    # Convert to percentage
    illumination = phase_fraction * 100

    # Determine phase name
    phase_name = _get_phase_name(illumination, target_date)

    # Check if near full moon
    is_full_moon_period = is_near_full_moon(target_date)

    return {
        'illumination': round(illumination, 1),
        'phase_name': phase_name,
        'is_full_moon_period': is_full_moon_period
    }


def _get_phase_name(illumination: float, target_date: date) -> str:
    """
    Determine moon phase name based on illumination and whether it's waxing or waning.

    Args:
        illumination: Moon illumination percentage (0-100)
        target_date: Date to check

    Returns:
        Phase name string
    """
    ts, eph = load_ephemeris()

    # Determine if moon is waxing or waning by checking if illumination
    # is increasing or decreasing
    t0 = ts.utc(target_date.year, target_date.month, target_date.day, 12, 0, 0)
    t1 = ts.utc(target_date.year, target_date.month, target_date.day + 1, 12, 0, 0)

    earth = eph['earth']
    moon = eph['moon']
    sun = eph['sun']

    # Calculate illumination for today and tomorrow using fraction_illuminated
    e0 = earth.at(t0)
    m0 = e0.observe(moon)
    illum0 = m0.fraction_illuminated(sun) * 100

    e1 = earth.at(t1)
    m1 = e1.observe(moon)
    illum1 = m1.fraction_illuminated(sun) * 100

    is_waxing = illum1 > illum0

    # Determine phase based on illumination and waxing/waning
    if illumination < 5:
        return "New Moon"
    elif illumination < 45:
        return "Waxing Crescent" if is_waxing else "Waning Crescent"
    elif 45 <= illumination < 55:
        return "First Quarter" if is_waxing else "Last Quarter"
    elif 55 <= illumination < 95:
        return "Waxing Gibbous" if is_waxing else "Waning Gibbous"
    else:  # illumination >= 95
        return "Full Moon"


def is_near_full_moon(target_date: date, days_threshold: int = 3) -> bool:
    """
    Check if a date is within a certain number of days from full moon.

    Args:
        target_date: Date to check
        days_threshold: Number of days before/after full moon to consider (default: 3)

    Returns:
        True if within threshold days of full moon, False otherwise

    Examples:
        >>> is_near_full_moon(date(2025, 1, 13))  # Full moon date
        True
        >>> is_near_full_moon(date(2025, 1, 29))  # New moon date
        False
    """
    ts, eph = load_ephemeris()

    # Define search window (±7 days to ensure we find nearby full moon)
    t0 = ts.utc(
        target_date.year,
        target_date.month,
        target_date.day - 7,
        0, 0, 0
    )
    t1 = ts.utc(
        target_date.year,
        target_date.month,
        target_date.day + 7,
        23, 59, 59
    )

    # Find moon phases in the window
    times, phases = almanac.find_discrete(t0, t1, almanac.moon_phases(eph))

    # Check each phase to see if it's a full moon within threshold
    for time, phase in zip(times, phases):
        if phase == 2:  # 2 = Full Moon (0=New, 1=First Quarter, 2=Full, 3=Last Quarter)
            full_moon_date = time.utc_datetime().date()
            days_diff = abs((target_date - full_moon_date).days)

            if days_diff <= days_threshold:
                return True

    return False


def calculate_moonrise_moonset(
    latitude: float,
    longitude: float,
    target_date: date
) -> Dict[str, Any]:
    """
    Calculate moonrise and moonset times with directions for a given location and date.

    This function computes the exact times of moonrise and moonset, along with
    the azimuth (compass direction) where the moon will rise/set.

    Args:
        latitude: Latitude in decimal degrees (-90 to 90)
                 Positive = North, Negative = South
        longitude: Longitude in decimal degrees (-180 to 180)
                  Positive = East, Negative = West
        target_date: Date for which to calculate moonrise/moonset

    Returns:
        Dictionary containing:
        {
            'moonrise': {
                'moonrise_time': datetime object (timezone-aware) or None,
                'moonrise_azimuth': float (degrees, 0-360) or None,
                'moonrise_direction': str (compass direction) or None
            },
            'moonset': {
                'moonset_time': datetime object (timezone-aware) or None,
                'moonset_azimuth': float (degrees, 0-360) or None,
                'moonset_direction': str (compass direction) or None
            }
        }

    Raises:
        ValueError: If latitude or longitude are out of valid ranges

    Examples:
        >>> result = calculate_moonrise_moonset(51.5074, -0.1278, date(2025, 1, 13))
        >>> if result['moonrise'] is not None:
        ...     print(result['moonrise']['moonrise_direction'])
        'NE'
    """
    # Validate inputs
    if not -90 <= latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90 degrees")

    if not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180 degrees")

    # Load ephemeris data
    ts, eph = load_ephemeris()

    # Create location
    topos = Topos(
        latitude_degrees=latitude,
        longitude_degrees=longitude
    )
    location = eph['earth'] + topos

    # Define the time range for the target date (full 24 hours)
    t0 = ts.utc(target_date.year, target_date.month, target_date.day, 0, 0, 0)
    t1 = ts.utc(target_date.year, target_date.month, target_date.day, 23, 59, 59)

    # Find moonrise and moonset times
    times, events = almanac.find_discrete(t0, t1, almanac.risings_and_settings(eph, eph['moon'], topos))

    # Parse results
    moonrise_time = None
    moonset_time = None

    for time, event in zip(times, events):
        if event == 1:  # Rising
            moonrise_time = time
        elif event == 0:  # Setting
            moonset_time = time

    # Calculate azimuth for moonrise if it exists
    moonrise_data = None
    if moonrise_time is not None:
        moon = eph['moon']
        moonrise_astrometric = location.at(moonrise_time).observe(moon)
        moonrise_alt, moonrise_az, _ = moonrise_astrometric.apparent().altaz()

        moonrise_data = {
            'moonrise_time': moonrise_time.utc_datetime(),
            'moonrise_azimuth': moonrise_az.degrees,
            'moonrise_direction': get_compass_direction(moonrise_az.degrees)
        }

    # Calculate azimuth for moonset if it exists
    moonset_data = None
    if moonset_time is not None:
        moon = eph['moon']
        moonset_astrometric = location.at(moonset_time).observe(moon)
        moonset_alt, moonset_az, _ = moonset_astrometric.apparent().altaz()

        moonset_data = {
            'moonset_time': moonset_time.utc_datetime(),
            'moonset_azimuth': moonset_az.degrees,
            'moonset_direction': get_compass_direction(moonset_az.degrees)
        }

    # Build result dictionary
    result = {
        'moonrise': moonrise_data,
        'moonset': moonset_data
    }

    return result
