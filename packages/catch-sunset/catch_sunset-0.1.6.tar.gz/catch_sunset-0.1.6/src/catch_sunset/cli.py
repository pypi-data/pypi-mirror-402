"""
Command-line interface for catch-sunset.

This module provides a Click-based CLI for checking sunset, sunrise,
moonrise, and moonset times with alert suggestions.
"""
import click
import socket
from datetime import date, timedelta, datetime
from typing import Optional, Tuple
from zoneinfo import ZoneInfo
from catch_sunset.astronomy import calculate_sunset_sunrise
from catch_sunset.moon import (
    calculate_moon_phase,
    is_near_full_moon,
    calculate_moonrise_moonset
)
from catch_sunset.alerts import calculate_alert_time, format_alert_suggestion
from catch_sunset.gps import get_current_coordinates, get_coordinates_manual
from catch_sunset.ntfy_alarm import send_alarm
from catch_sunset.cloudysky import get_cloud_cover_at_time, get_cloud_cover_emoji
from catch_sunset.config import get_ntfy_config
from console import fg

# Default location: Prague, Czech Republic (fallback if GPS fails)
DEFAULT_LATITUDE = 50.0755
DEFAULT_LONGITUDE = 14.4378
DEFAULT_TIMEZONE = "Europe/Prague"

# Default ntfy.sh configuration
DEFAULT_NTFY_SERVER = "https://ntfy.sh"
DEFAULT_NTFY_TOPIC = socket.gethostname()


def _get_coordinates(lat: Optional[float], lon: Optional[float]) -> Tuple[float, float, str]:
    """
    Get coordinates from manual input or GPS auto-detection.

    Args:
        lat: Manual latitude (None to use GPS)
        lon: Manual longitude (None to use GPS)

    Returns:
        Tuple of (latitude, longitude, source_description)
    """
    # If both coordinates provided, use manual input
    if lat is not None and lon is not None:
        coords = get_coordinates_manual(lat, lon)
        return coords.latitude, coords.longitude, "Manual"

    # If only one coordinate provided, that's an error
    if lat is not None or lon is not None:
        raise click.UsageError(
            "Both --lat and --lon must be provided together, or neither for GPS auto-detection"
        )

    # Try GPS auto-detection
    print(fg.steelblue, end="\r")
    click.echo("... 📡 Detecting location via IP geolocation...", err=True)
    coords = get_current_coordinates(fallback_to_ip=True)

    if coords:
        source_info = f"GPS ({coords.source}, ±{coords.precision_meters/1000:.1f}km)"
        click.echo(f"... ✓ Location detected: {coords.latitude:.4f}°, {coords.longitude:.4f}°\n", err=True)
        return coords.latitude, coords.longitude, source_info

    # Fallback to default location
    click.echo(
        f"⚠ Could not detect location. Using default: Prague, Czech Republic\n"
        f"  (Use --lat and --lon to specify a different location)\n",
        err=True
    )
    print(fg.default, end="\r")
    return DEFAULT_LATITUDE, DEFAULT_LONGITUDE, "Default (Prague)"


@click.group(invoke_without_command=True)
@click.version_option()
@click.pass_context
def cli(ctx):
    """
    Catch Sunset - Track sunset, sunrise, moonrise, and moonset events.

    This tool helps you find the best times to observe astronomical events
    with alert suggestions for preparation time.

    By default, your location is auto-detected via IP geolocation.
    Use --lat and --lon options to manually specify coordinates.
    """
    if ctx.invoked_subcommand is None:
        ctx.invoke(today)


@cli.command()
@click.option('--lat', type=float, default=None,
              help='Latitude in decimal degrees (-90 to 90). Auto-detected if not provided.')
@click.option('--lon', type=float, default=None,
              help='Longitude in decimal degrees (-180 to 180). Auto-detected if not provided.')
@click.option('--alert-time', default=30, type=int, help='Alert buffer time in minutes (default: 30)')
@click.option('-s', '--alarm-sunrise', is_flag=True, help='Set alarm for sunrise')
@click.option('-S', '--alarm-sunset', is_flag=True, help='Set alarm for sunset')
@click.option('-m', '--alarm-moonrise', is_flag=True, help='Set alarm for moonrise')
@click.option('-M', '--alarm-moonset', is_flag=True, help='Set alarm for moonset')
@click.option('--ntfy-server', default=None, help=f'Ntfy server URL (default: from config or {DEFAULT_NTFY_SERVER})')
@click.option('--ntfy-topic', default=None, help=f'Ntfy topic to send alarms to (default: from config or hostname)')
@click.option('--cloud-threshold', default=None, type=int, help='Cloud cover threshold percentage (0-100) for sending alarms (default: from config or 50)')
@click.option('--config', default=None, help='Path to config file (default: ~/.config/influxdb/totalconfig.conf)')
def today(lat: Optional[float], lon: Optional[float], alert_time: int, alarm_sunrise: bool, alarm_sunset: bool, alarm_moonrise: bool, alarm_moonset: bool, ntfy_server: Optional[str], ntfy_topic: Optional[str], cloud_threshold: Optional[int], config: Optional[str]):
    """
    Show today's sunset/sunrise and moonrise/moonset (if near full moon).

    Location is auto-detected via IP geolocation by default.
    Use --lat and --lon to manually specify coordinates.

    Ntfy credentials are read from config file (~/.config/influxdb/totalconfig.conf)
    from the [ntfy] section with keys: server, username, password, topic.

    Examples:
        catch-sunset today
        catch-sunset today --lat 51.5074 --lon -0.1278 --alert-time 30
        catch-sunset today -s -S --ntfy-topic mysunset
        catch-sunset today -s -S -m -M --ntfy-server https://ntfy.example.com
    """
    latitude, longitude, source = _get_coordinates(lat, lon)
    target_date = date.today()

    # Get config from file, with CLI options overriding
    ntfy_config = get_ntfy_config(
        config_path=config,
        fallback_server=ntfy_server or DEFAULT_NTFY_SERVER,
        fallback_topic=ntfy_topic or DEFAULT_NTFY_TOPIC,
        fallback_cloud_threshold=cloud_threshold if cloud_threshold is not None else 50
    )

    # CLI options override config file if provided
    if ntfy_server:
        ntfy_config['server'] = ntfy_server
        # Clear credentials if server is overridden - don't use config credentials for different server
        ntfy_config['username'] = ''
        ntfy_config['password'] = ''
    if ntfy_topic:
        ntfy_config['topic'] = ntfy_topic
    if cloud_threshold is not None:
        ntfy_config['cloud_cover_threshold'] = cloud_threshold

    _display_events(latitude, longitude, target_date, alert_time, source, alarm_sunrise, alarm_sunset, alarm_moonrise, alarm_moonset, ntfy_config)


@cli.command()
@click.option('--lat', type=float, default=None,
              help='Latitude in decimal degrees (-90 to 90). Auto-detected if not provided.')
@click.option('--lon', type=float, default=None,
              help='Longitude in decimal degrees (-180 to 180). Auto-detected if not provided.')
@click.option('--alert-time', default=30, type=int, help='Alert buffer time in minutes (default: 30)')
@click.option('-s', '--alarm-sunrise', is_flag=True, help='Set alarm for sunrise')
@click.option('-S', '--alarm-sunset', is_flag=True, help='Set alarm for sunset')
@click.option('-m', '--alarm-moonrise', is_flag=True, help='Set alarm for moonrise')
@click.option('-M', '--alarm-moonset', is_flag=True, help='Set alarm for moonset')
@click.option('--ntfy-server', default=None, help=f'Ntfy server URL (default: from config or {DEFAULT_NTFY_SERVER})')
@click.option('--ntfy-topic', default=None, help=f'Ntfy topic to send alarms to (default: from config or hostname)')
@click.option('--cloud-threshold', default=None, type=int, help='Cloud cover threshold percentage (0-100) for sending alarms (default: from config or 50)')
@click.option('--config', default=None, help='Path to config file (default: ~/.config/influxdb/totalconfig.conf)')
def tomorrow(lat: Optional[float], lon: Optional[float], alert_time: int, alarm_sunrise: bool, alarm_sunset: bool, alarm_moonrise: bool, alarm_moonset: bool, ntfy_server: Optional[str], ntfy_topic: Optional[str], cloud_threshold: Optional[int], config: Optional[str]):
    """
    Show tomorrow's sunset/sunrise and moonrise/moonset (if near full moon).

    Location is auto-detected via IP geolocation by default.
    Use --lat and --lon to manually specify coordinates.

    Examples:
        catch-sunset tomorrow
        catch-sunset tomorrow --lat 51.5074 --lon -0.1278
        catch-sunset tomorrow -s -S
    """
    latitude, longitude, source = _get_coordinates(lat, lon)
    target_date = date.today() + timedelta(days=1)

    # Get config from file, with CLI options overriding
    ntfy_config = get_ntfy_config(
        config_path=config,
        fallback_server=ntfy_server or DEFAULT_NTFY_SERVER,
        fallback_topic=ntfy_topic or DEFAULT_NTFY_TOPIC,
        fallback_cloud_threshold=cloud_threshold if cloud_threshold is not None else 50
    )

    # CLI options override config file if provided
    if ntfy_server:
        ntfy_config['server'] = ntfy_server
        # Clear credentials if server is overridden - don't use config credentials for different server
        ntfy_config['username'] = ''
        ntfy_config['password'] = ''
    if ntfy_topic:
        ntfy_config['topic'] = ntfy_topic
    if cloud_threshold is not None:
        ntfy_config['cloud_cover_threshold'] = cloud_threshold

    _display_events(latitude, longitude, target_date, alert_time, source, alarm_sunrise, alarm_sunset, alarm_moonrise, alarm_moonset, ntfy_config)


@cli.command()
@click.option('--lat', type=float, default=None,
              help='Latitude in decimal degrees (-90 to 90). Auto-detected if not provided.')
@click.option('--lon', type=float, default=None,
              help='Longitude in decimal degrees (-180 to 180). Auto-detected if not provided.')
@click.option('--start-date', type=click.DateTime(formats=['%Y-%m-%d']), required=True,
              help='Start date (YYYY-MM-DD)')
@click.option('--end-date', type=click.DateTime(formats=['%Y-%m-%d']), required=True,
              help='End date (YYYY-MM-DD)')
@click.option('--alert-time', default=30, type=int, help='Alert buffer time in minutes (default: 30)')
@click.option('-s', '--alarm-sunrise', is_flag=True, help='Set alarm for sunrise')
@click.option('-S', '--alarm-sunset', is_flag=True, help='Set alarm for sunset')
@click.option('-m', '--alarm-moonrise', is_flag=True, help='Set alarm for moonrise')
@click.option('-M', '--alarm-moonset', is_flag=True, help='Set alarm for moonset')
@click.option('--ntfy-server', default=None, help=f'Ntfy server URL (default: from config or {DEFAULT_NTFY_SERVER})')
@click.option('--ntfy-topic', default=None, help=f'Ntfy topic to send alarms to (default: from config or hostname)')
@click.option('--cloud-threshold', default=None, type=int, help='Cloud cover threshold percentage (0-100) for sending alarms (default: from config or 50)')
@click.option('--config', default=None, help='Path to config file (default: ~/.config/influxdb/totalconfig.conf)')
def range_cmd(lat: Optional[float], lon: Optional[float], start_date: datetime, end_date: datetime, alert_time: int, alarm_sunrise: bool, alarm_sunset: bool, alarm_moonrise: bool, alarm_moonset: bool, ntfy_server: Optional[str], ntfy_topic: Optional[str], cloud_threshold: Optional[int], config: Optional[str]):
    """
    Show events for a date range.

    Location is auto-detected via IP geolocation by default.
    Use --lat and --lon to manually specify coordinates.

    Examples:
        catch-sunset range --start-date 2025-01-15 --end-date 2025-01-20
        catch-sunset range --lat 51.5074 --lon -0.1278 --start-date 2025-01-15 --end-date 2025-01-20
        catch-sunset range --start-date 2025-01-15 --end-date 2025-01-20 -s -S
    """
    latitude, longitude, source = _get_coordinates(lat, lon)
    current = start_date.date()
    end = end_date.date()

    if current > end:
        click.echo("Error: Start date must be before or equal to end date", err=True)
        return

    # Get config from file, with CLI options overriding
    ntfy_config = get_ntfy_config(
        config_path=config,
        fallback_server=ntfy_server or DEFAULT_NTFY_SERVER,
        fallback_topic=ntfy_topic or DEFAULT_NTFY_TOPIC,
        fallback_cloud_threshold=cloud_threshold if cloud_threshold is not None else 50
    )

    # CLI options override config file if provided
    if ntfy_server:
        ntfy_config['server'] = ntfy_server
        # Clear credentials if server is overridden - don't use config credentials for different server
        ntfy_config['username'] = ''
        ntfy_config['password'] = ''
    if ntfy_topic:
        ntfy_config['topic'] = ntfy_topic
    if cloud_threshold is not None:
        ntfy_config['cloud_cover_threshold'] = cloud_threshold

    while current <= end:
        click.echo(f"\n{'='*70}")
        _display_events(latitude, longitude, current, alert_time, source, alarm_sunrise, alarm_sunset, alarm_moonrise, alarm_moonset, ntfy_config)
        current += timedelta(days=1)


def _to_local_time(utc_time: datetime) -> datetime:
    """
    Convert UTC time to Prague local time.

    Args:
        utc_time: datetime in UTC timezone

    Returns:
        datetime in Prague timezone (automatically handles DST)
    """
    prague_tz = ZoneInfo(DEFAULT_TIMEZONE)
    return utc_time.astimezone(prague_tz)


def _format_cloud_info(cloud_data: dict) -> str:
    """
    Format cloud cover information for display.

    Args:
        cloud_data: Dictionary from get_cloud_cover_at_time

    Returns:
        Formatted string with weather info and emoji
    """
    if cloud_data is None:
        return "   ☁️  Weather: unavailable"

    status_emoji = get_cloud_cover_emoji(cloud_data['cloud_cover'])
    rain_info = f", rain: {cloud_data['rain']}mm" if cloud_data['rain'] > 0 else ""

    cloud_data_color = cloud_data['status'].upper()
    if cloud_data_color == "CLEAR":cloud_data_color = f"{fg.green}{cloud_data_color}{fg.default}"
    return (f"   {status_emoji} Sky {cloud_data_color} "
            f"({cloud_data['cloud_cover']:.0f}% clouds, "
            f"{cloud_data['temperature']:.1f}°C{rain_info})")


def _display_events(lat: float, lon: float, target_date: date, alert_time_minutes: int, source: str = "Manual", alarm_sunrise: bool = False, alarm_sunset: bool = False, alarm_moonrise: bool = False, alarm_moonset: bool = False, ntfy_config: dict = None):
    """
    Display astronomical events for a specific date.

    Args:
        lat: Latitude
        lon: Longitude
        target_date: Date to check
        alert_time_minutes: Buffer time for alerts in minutes
        source: Source of coordinates (e.g., "GPS", "Manual", "Default")
        alarm_sunrise: If True, send alarm for sunrise
        alarm_sunset: If True, send alarm for sunset
        alarm_moonrise: If True, send alarm for moonrise
        alarm_moonset: If True, send alarm for moonset
        ntfy_config: Dictionary with ntfy configuration (server, username, password, topic)
    """
    if ntfy_config is None:
        ntfy_config = {'server': DEFAULT_NTFY_SERVER, 'username': '', 'password': '', 'topic': DEFAULT_NTFY_TOPIC}

    # Build full topic URL
    full_topic_url = f"{ntfy_config['server'].rstrip('/')}/{ntfy_config['topic']}"
    print(fg.steelblue, end="\r")
    click.echo(f"... 📅 Date: {target_date.strftime('%Y-%m-%d (%A)')}")
    click.echo(f"... 📍 Location: {lat:.4f}°, {lon:.4f}° ({source})")
    click.echo(f"... ⏰ Alert buffer: {alert_time_minutes} minutes\n")
    print(fg.default, end="\r")

    # Get current time in local timezone for filtering past events
    current_time = datetime.now().astimezone()

    try:
        # Get sunset/sunrise
        sun_data = calculate_sunset_sunrise(lat, lon, target_date)

        # Display sunrise
        sunrise_info = sun_data['sunrise']
        sunrise_time_utc = sunrise_info['sunrise_time']
        sunrise_time = _to_local_time(sunrise_time_utc)
        sunrise_alert_utc = calculate_alert_time(sunrise_time_utc, alert_time_minutes)
        sunrise_alert = _to_local_time(sunrise_alert_utc)

        # Only display sunrise if it hasn't occurred yet
        if sunrise_time > current_time:
            # Get cloud cover for sunrise
            sunrise_cloud = get_cloud_cover_at_time(lat, lon, sunrise_time)

            click.echo("🌅 SUNRISE")
            click.echo(f"   Time: {sunrise_time.strftime('%H:%M:%S %Z')} ...    ⏰ Alarm time: {sunrise_alert.strftime('%H:%M:%S %Z')}")
            click.echo(f"   Direction: {sunrise_info['sunrise_direction']} ({sunrise_info['sunrise_azimuth']:.1f}°)")
            click.echo(_format_cloud_info(sunrise_cloud))
            #click.echo(f"")

            if alarm_sunrise and sunrise_cloud['cloud_cover'] <= ntfy_config['cloud_cover_threshold']:
                try:
                    message = f"🌅 Sunrise in {alert_time_minutes} minutes at {sunrise_time.strftime('%H:%M')}"
                    if ntfy_config['username'] == '' or ntfy_config['password'] == '':
                        send_alarm(message, sunrise_alert, full_topic_url,
                                   title="Sunrise Alert")
                    else:
                        send_alarm(message, sunrise_alert, full_topic_url,
                                   title="Sunrise Alert",
                                   username=ntfy_config['username'],
                                   password=ntfy_config['password'])
                        print(ntfy_config)
                    click.echo(f"   ✓ Alarm scheduled via {full_topic_url} ")
                except Exception as e:
                    click.echo(f"   ✗ Failed to schedule alarm: {e}", err=True)

            click.echo()

        # Display sunset
        sunset_info = sun_data['sunset']
        sunset_time_utc = sunset_info['sunset_time']
        sunset_time = _to_local_time(sunset_time_utc)
        sunset_alert_utc = calculate_alert_time(sunset_time_utc, alert_time_minutes)
        sunset_alert = _to_local_time(sunset_alert_utc)

        # Only display sunset if it hasn't occurred yet
        if sunset_time > current_time:
            # Get cloud cover for sunset
            sunset_cloud = get_cloud_cover_at_time(lat, lon, sunset_time)

            click.echo("🌇 SUNSET")
            click.echo(f"   Time: {sunset_time.strftime('%H:%M:%S %Z')} ...    ⏰ Alarm time: {sunset_alert.strftime('%H:%M:%S %Z')}")
            click.echo(f"   Direction: {sunset_info['sunset_direction']} ({sunset_info['sunset_azimuth']:.1f}°)")
            click.echo(_format_cloud_info(sunset_cloud))
            #click.echo(f"")

            if alarm_sunset and sunset_cloud['cloud_cover'] <= ntfy_config['cloud_cover_threshold']:
                try:
                    message = f"🌇 Sunset in {alert_time_minutes} minutes at {sunset_time.strftime('%H:%M')}"
                    send_alarm(message, sunset_alert, full_topic_url,
                             title="Sunset Alert",
                             username=ntfy_config['username'],
                             password=ntfy_config['password'])
                    click.echo(f"   ✓ Alarm scheduled via {full_topic_url}")
                except Exception as e:
                    click.echo(f"   ✗ Failed to schedule alarm: {e}", err=True)

            click.echo()

        # Check moon phase
        moon_phase = calculate_moon_phase(target_date)
        click.echo(f"🌙 MOON PHASE: {moon_phase['phase_name']} ({moon_phase['illumination']:.1f}% illuminated)")

        # If near full moon, show moonrise/moonset
        #if moon_phase['is_full_moon_period']
        if moon_phase['illumination'] > 5:
            if moon_phase['is_full_moon_period']: click.echo("   ⭐ Near full moon - showing moonrise/moonset:\n")

            moon_data = calculate_moonrise_moonset(lat, lon, target_date)

            if moon_data['moonrise'] is not None:
                moonrise_info = moon_data['moonrise']
                moonrise_time_utc = moonrise_info['moonrise_time']
                moonrise_time = _to_local_time(moonrise_time_utc)
                moonrise_alert_utc = calculate_alert_time(moonrise_time_utc, alert_time_minutes)
                moonrise_alert = _to_local_time(moonrise_alert_utc)

                # Only display moonrise if it hasn't occurred yet
                if moonrise_time > current_time and (moonrise_time < sunrise_time or moonrise_time > sunset_time ):
                    # Get cloud cover for moonrise
                    moonrise_cloud = get_cloud_cover_at_time(lat, lon, moonrise_time)

                    #click.echo("   🌕 MOONRISE")↑
                    click.echo(f"  {fg.yellow} ⟰ MOONRISE{fg.default}")
                    click.echo(f"      Time: {moonrise_time.strftime('%H:%M:%S %Z')} ...       ⏰ Alarm time: {moonrise_alert.strftime('%H:%M:%S %Z')}")
                    click.echo(f"      Direction: {moonrise_info['moonrise_direction']} ({moonrise_info['moonrise_azimuth']:.1f}°)")
                    click.echo(f"   {_format_cloud_info(moonrise_cloud)}")
                    #click.echo(f"")

                    if alarm_moonrise and moonrise_cloud['cloud_cover'] <= ntfy_config['cloud_cover_threshold']:
                        try:
                            #message = f"🌕 Moonrise in {alert_time_minutes} minutes at {moonrise_time.strftime('%H:%M')}"
                            message = f"🌕 Moonrise in {alert_time_minutes} minutes at {moonrise_time.strftime('%H:%M')}"
                            send_alarm(message, moonrise_alert, full_topic_url,
                                     title="Moonrise Alert",
                                     username=ntfy_config['username'],
                                     password=ntfy_config['password'])
                            click.echo(f"      ✓ Alarm scheduled via {full_topic_url}")
                        except Exception as e:
                            click.echo(f"      ✗ Failed to schedule alarm: {e}", err=True)

                    click.echo()

            if moon_data['moonset'] is not None:
                moonset_info = moon_data['moonset']
                moonset_time_utc = moonset_info['moonset_time']
                moonset_time = _to_local_time(moonset_time_utc)
                moonset_alert_utc = calculate_alert_time(moonset_time_utc, alert_time_minutes)
                moonset_alert = _to_local_time(moonset_alert_utc)

                # Only display moonset if it hasn't occurred yet
                if moonset_time > current_time and (moonset_time < sunrise_time or moonset_time > sunset_time ):
                    # Get cloud cover for moonset
                    moonset_cloud = get_cloud_cover_at_time(lat, lon, moonset_time)

                    #click.echo("   🌑 MOONSET")
                    click.echo(f"    {fg.orange}⟱ MOONSET{fg.default}")
                    click.echo(f"      Time: {moonset_time.strftime('%H:%M:%S %Z')} ...       ⏰ Alarm time: {moonset_alert.strftime('%H:%M:%S %Z')}")
                    click.echo(f"      Direction: {moonset_info['moonset_direction']} ({moonset_info['moonset_azimuth']:.1f}°)")
                    click.echo(f"   {_format_cloud_info(moonset_cloud)}")
                    #click.echo(f"")

                    if alarm_moonset  and moonset_cloud['cloud_cover'] <= ntfy_config['cloud_cover_threshold']:
                        try:
                            message = f"🌑 Moonset in {alert_time_minutes} minutes at {moonset_time.strftime('%H:%M')}"
                            send_alarm(message, moonset_alert, full_topic_url,
                                     title="Moonset Alert",
                                     username=ntfy_config['username'],
                                     password=ntfy_config['password'])
                            click.echo(f"      ✓ Alarm scheduled via {full_topic_url}")
                        except Exception as e:
                            click.echo(f"      ✗ Failed to schedule alarm: {e}", err=True)

                    click.echo()
        else:
            click.echo()

        # Suggest alarm options if none were set
        if not (alarm_sunrise or alarm_sunset or alarm_moonrise or alarm_moonset):
            click.echo("💡 Tip: Set alarms with -s (sunrise), -S (sunset), -m (moonrise), -M (moonset)")

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
    except RuntimeError as e:
        click.echo(f"Warning: {e}", err=True)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)


if __name__ == '__main__':
    cli()
