"""
Configuration module for reading ntfy settings from config file.

This module provides functionality to read ntfy server, credentials, and topic
from a configuration file using Python's configparser.
"""
import os
from configparser import ConfigParser
from pathlib import Path
from typing import Optional, Dict


def read_ntfy_config(config_path: Optional[str] = None) -> Dict[str, Optional[str]]:
    """
    Read ntfy configuration from config file.

    Args:
        config_path: Path to configuration file. If None, defaults to
                    ~/.config/influxdb/totalconfig.conf

    Returns:
        Dictionary with keys: server, username, password, topic, cloud_cover_threshold
        Values will be None if not found or if config file doesn't exist
    """
    if config_path is None:
        config_path = os.path.expanduser("~/.config/influxdb/totalconfig.conf")
    else:
        config_path = os.path.expanduser(config_path)

    # Check if config file exists
    if not os.path.exists(config_path):
        return {
            'server': None,
            'username': None,
            'password': None,
            'topic': None,
            'cloud_cover_threshold': None
        }

    result = {
        'server': None,
        'username': None,
        'password': None,
        'topic': None,
        'cloud_cover_threshold': None
    }

    try:
        config = ConfigParser()
        config.read(config_path)

        # Check if ntfy section exists
        if 'ntfy sunset' in config:
            ntfy_section = config['ntfy sunset']

            # Read each configuration value
            for key in ['server', 'username', 'password', 'topic']:
                if key in ntfy_section:
                    value = ntfy_section[key].strip()
                    if value:  # Only set if non-empty
                        result[key] = value

            # Read cloud_cover_threshold as integer
            if 'cloud_cover_threshold' in ntfy_section:
                try:
                    threshold = int(ntfy_section['cloud_cover_threshold'].strip())
                    if 0 <= threshold <= 100:
                        result['cloud_cover_threshold'] = threshold
                except ValueError:
                    pass

    except Exception:
        # If config parsing fails, return empty result
        pass

    return result


def get_ntfy_config(
    config_path: Optional[str] = None,
    fallback_server: str = "https://ntfy.sh",
    fallback_topic: str = "default",
    fallback_cloud_threshold: int = 50
) -> Dict:
    """
    Get ntfy configuration with fallback values.

    Args:
        config_path: Path to configuration file
        fallback_server: Server to use if not in config
        fallback_topic: Topic to use if not in config
        fallback_cloud_threshold: Cloud cover threshold (0-100) to use if not in config

    Returns:
        Dictionary with keys: server, username, password, topic, cloud_cover_threshold
        username and password may be empty strings if not configured
    """
    config = read_ntfy_config(config_path)

    return {
        'server': config['server'] or fallback_server,
        'username': config['username'] or '',
        'password': config['password'] or '',
        'topic': config['topic'] or fallback_topic,
        'cloud_cover_threshold': config['cloud_cover_threshold'] if config['cloud_cover_threshold'] is not None else fallback_cloud_threshold
    }
