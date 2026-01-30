"""
Module for sending alarms via ntfy.sh service.

This module provides functionality to schedule notifications using the ntfy.sh
push notification service with delayed delivery.
"""
import requests
from datetime import datetime
from typing import Optional


def send_alarm(
    message: str,
    schedule_time: datetime,
    topic: str,
    title: Optional[str] = None,
    priority: int = 4,
    username: Optional[str] = None,
    password: Optional[str] = None
) -> bool:
    """
    Send a scheduled alarm via ntfy.sh.

    Args:
        message: The notification message content
        schedule_time: When the notification should be delivered
        topic: The ntfy topic URL (e.g., "https://ntfy.sh/mytopic")
        title: Optional notification title
        priority: Priority level 1-5 (default: 4 - high)
        username: Optional username for authentication
        password: Optional password for authentication

    Returns:
        True if notification was successfully scheduled, False otherwise

    Raises:
        requests.RequestException: If the HTTP request fails
    """
    #print(topic)
    # Ensure topic has the full URL
    if not topic.startswith("http"):
        if not topic.startswith("ntfy.sh/"):
            topic = f"ntfy.sh/{topic}"
        topic = f"https://{topic}"

    # Format the schedule time for ntfy
    # ntfy accepts: Unix timestamp (most reliable), duration (e.g., "30m"), or natural language (e.g., "10am")
    # Using Unix timestamp for precision and timezone handling
    unix_timestamp = int(schedule_time.timestamp())

    # Build headers
    headers = {
        "At": str(unix_timestamp),
        "Priority": str(priority)
    }

    if title:
        headers["Title"] = title

    # Prepare authentication if provided
    auth = None
    if username and password:
        auth = (username, password)

    #print(topic)
    try:
        response = requests.post(
            topic,
            data=message.encode('utf-8'),
            headers=headers,
            auth=auth,
            timeout=10
        )
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        raise requests.RequestException(f"Failed to send ntfy alarm: {e}")


# def send_alarm_simple(
#     message: str,
#     at_string: str,
#     topic: str = "ntfy.sh/kuk",
#     title: Optional[str] = None,
#     priority: int = 4
# ) -> bool:
#     """
#     Send a scheduled alarm via ntfy.sh using a natural language time string.

#     This is a simpler version that accepts ntfy's natural language format.

#     Args:
#         message: The notification message content
#         at_string: When to deliver (e.g., "tomorrow, 10am", "in 30 minutes")
#         topic: The ntfy topic (default: "ntfy.sh/kuk")
#         title: Optional notification title
#         priority: Priority level 1-5 (default: 4 - high)

#     Returns:
#         True if notification was successfully scheduled, False otherwise

#     Raises:
#         requests.RequestException: If the HTTP request fails
#     """
#     # Ensure topic has the full URL
#     if not topic.startswith("http"):
#         if not topic.startswith("ntfy.sh/"):
#             topic = f"ntfy.sh/{topic}"
#         topic = f"https://{topic}"

#     # Build headers
#     headers = {
# #        "At": at_string,
#         "Priority": str(priority)
#     }

#     if title:
#         headers["Title"] = title

#     try:
#         response = requests.post(
#             topic,
#             data=message.encode('utf-8'),
#             headers=headers,
#             timeout=10
#         )
#         response.raise_for_status()
#         return True
#     except requests.RequestException as e:
#         raise requests.RequestException(f"Failed to send ntfy alarm: {e}")
