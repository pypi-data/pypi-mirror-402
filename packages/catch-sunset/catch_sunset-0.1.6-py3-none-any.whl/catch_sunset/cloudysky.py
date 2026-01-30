"""
Cloud cover and weather checking using Open-Meteo API.

This module provides functions to check cloud cover at specific times
for sunrise, sunset, moonrise, and moonset predictions.
"""
import click
import requests
import sys
from datetime import datetime
from typing import Optional, Dict, Any


def get_cloud_cover_at_time(lat: float, lon: float, target_time: datetime) -> Optional[Dict[str, Any]]:
    """
    Get cloud cover prediction for a specific time at given coordinates.

    Args:
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees
        target_time: Target datetime (should be timezone-aware)

    Returns:
        Dictionary with cloud cover data:
        {
            'cloud_cover': float,  # percentage 0-100
            'temperature': float,  # degrees Celsius
            'rain': float,        # mm
            'is_clear': bool,     # True if cloud_cover <= 25%
            'status': str         # 'clear' or 'cloudy'
        }
        Returns None if the API call fails.
    """
    # Format time for API (ISO 8601 format)
    # Open-Meteo expects format like: 2025-01-15T14:30
    time_str = target_time.strftime('%Y-%m-%dT%H:%M')

    # Get hourly forecast data
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&"
        f"hourly=cloud_cover,temperature_2m,rain&"
        f"timezone=auto"
    )

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Find the closest time in the hourly data
        hourly = data.get('hourly', {})
        times = hourly.get('time', [])
        cloud_covers = hourly.get('cloud_cover', [])
        temperatures = hourly.get('temperature_2m', [])
        rains = hourly.get('rain', [])

        # Find the closest matching time
        target_str = target_time.strftime('%Y-%m-%dT%H:00')  # Round to hour

        if target_str in times:
            idx = times.index(target_str)
            cloud_cover = cloud_covers[idx]
            temperature = temperatures[idx]
            rain = rains[idx]

            return {
                'cloud_cover': cloud_cover,
                'temperature': temperature,
                'rain': rain,
                'is_clear': cloud_cover <= 25,
                'status': 'clear' if cloud_cover <= 25 else 'cloudy'
            }

        return None

    except (KeyError, requests.RequestException, ValueError):
        return None


def get_current_cloud_cover(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    """
    Get current cloud cover at given coordinates.

    Args:
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees

    Returns:
        Dictionary with current cloud cover data (same format as get_cloud_cover_at_time).
        Returns None if the API call fails.
    """
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&"
        f"current=cloud_cover,temperature_2m,rain&timezone=auto"
    )

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        cloud_cover = data['current']['cloud_cover']
        temperature = data['current']['temperature_2m']
        rain = data['current']['rain']

        return {
            'cloud_cover': cloud_cover,
            'temperature': temperature,
            'rain': rain,
            'is_clear': cloud_cover <= 25,
            'status': 'clear' if cloud_cover <= 25 else 'cloudy'
        }

    except (KeyError, requests.RequestException):
        return None


def get_cloud_cover_emoji(cloud_cover: float) -> str:
    """
    Get an emoji representing cloud cover percentage.

    Args:
        cloud_cover: Cloud cover percentage (0-100)

    Returns:
        Emoji string representing the cloud cover level:
        - 0-10%: ☀️ (sunny)
        - 11-35%: 🌤️ (mostly sunny)
        - 36-65%: ⛅ (partly cloudy)
        - 66-90%: 🌥️ (mostly cloudy)
        - 91-100%: ☁️ (overcast)
    """
    if cloud_cover <= 10:
        return "☀️"
    elif cloud_cover <= 35:
        return "🌤️"
    elif cloud_cover <= 65:
        return "⛅"
    elif cloud_cover <= 90:
        return "🌥️"
    else:
        return "☁️"


@click.command()
@click.option('--lat', type=float, default=50.185, help='Latitude (default: 50.185)')
@click.option('--lon', type=float, default=14.676, help='Longitude (default: 14.676)')
def sky_check(lat: float, lon: float) -> None:
    """
    Check if the sky is clear or cloudy at given lat/lon using Open-Meteo API.
    Clear: cloud_cover <= 25%. Cloudy: >25%.
    """
    result = get_current_cloud_cover(lat, lon)

    if result is None:
        print("Error: Could not fetch weather data.", file=sys.stderr)
        sys.exit(1)

    print(f"Sky at lat={lat}, lon={lon}: {result['status'].upper()} "
          f"(cloud cover: {result['cloud_cover']}%, "
          f"temperature: {result['temperature']}°C, "
          f"rain: {result['rain']}mm)")
