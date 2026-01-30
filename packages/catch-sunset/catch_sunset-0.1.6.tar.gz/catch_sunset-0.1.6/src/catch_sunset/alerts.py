"""
Alerts module for calculating when to set alarms before astronomical events.

This module provides functions to calculate alert times before sunrise, sunset,
moonrise, and moonset events, with configurable buffer times for preparation.
"""
from datetime import datetime, timedelta
from typing import Optional


def calculate_alert_time(event_time: datetime, buffer_minutes: int) -> datetime:
    """
    Calculate the alert time before an astronomical event.

    Args:
        event_time: The datetime of the astronomical event (sunrise, sunset, etc.)
        buffer_minutes: Number of minutes before the event to set the alert

    Returns:
        datetime: The time when the alert should trigger

    Raises:
        ValueError: If buffer_minutes is negative

    Examples:
        >>> event = datetime(2025, 1, 15, 16, 30, 0, tzinfo=timezone.utc)
        >>> alert = calculate_alert_time(event, 30)
        >>> print(alert)
        2025-01-15 16:00:00+00:00
    """
    if buffer_minutes < 0:
        raise ValueError("Buffer time must be non-negative")

    alert_time = event_time - timedelta(minutes=buffer_minutes)
    return alert_time


def format_alert_suggestion(
    event_type: str,
    event_time: datetime,
    alert_time: datetime,
    direction: str,
    buffer_minutes: Optional[int] = None
) -> str:
    """
    Format a human-readable alert suggestion for an astronomical event.

    Args:
        event_type: Type of event ('sunrise', 'sunset', 'moonrise', 'moonset')
        event_time: The datetime when the event occurs
        alert_time: The datetime when to set the alarm
        direction: Compass direction where event occurs (e.g., 'SE', 'SW')
        buffer_minutes: Optional buffer time in minutes (will be calculated if not provided)

    Returns:
        str: Formatted alert suggestion message

    Examples:
        >>> event = datetime(2025, 1, 15, 16, 30, 0, tzinfo=timezone.utc)
        >>> alert = datetime(2025, 1, 15, 16, 0, 0, tzinfo=timezone.utc)
        >>> suggestion = format_alert_suggestion('sunset', event, alert, 'SW')
        >>> print(suggestion)
        SUNSET at 16:30:00 UTC in direction SW
        Set alarm for: 16:00:00 UTC (30 minutes before)
    """
    # Calculate buffer time if not provided
    if buffer_minutes is None:
        time_diff = event_time - alert_time
        buffer_minutes = int(time_diff.total_seconds() / 60)

    # Format times
    event_time_str = event_time.strftime("%H:%M:%S")
    alert_time_str = alert_time.strftime("%H:%M:%S")

    # Get timezone name
    tz_name = event_time.tzname() or "UTC"

    # Build suggestion message
    suggestion = (
        f"{event_type.upper()} at {event_time_str} {tz_name} in direction {direction}\n"
        f"Set alarm for: {alert_time_str} {tz_name} ({buffer_minutes} minutes before)"
    )

    return suggestion
