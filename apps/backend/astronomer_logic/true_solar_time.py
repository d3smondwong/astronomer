"""
真太阳时 True Solar Time Conversion

Converts standard wall-clock time to True Solar Time (TST, 真太阳时) using:
1. Equation of Time (均时差) — accounts for Earth's elliptical orbit and axial tilt (±14-16 min)
2. Longitude Correction (经度修正) — 4 minutes per degree from the standard meridian

Returns a Solar object (lunar-python) ready to be converted to a Lunar object,
which is the entry point for all downstream BaZi calculations.
"""

import math
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from lunar_python import Solar
from timezonefinder import TimezoneFinder


def get_true_solar_time(birth_datetime: datetime, latitude: float, longitude: float) -> Solar:
    """
    Convert standard wall-clock birth time to True Solar Time (真太阳时).

    Args:
        birth_datetime: Wall-clock birth datetime (naive, no tzinfo).
        latitude:       Birth location latitude in decimal degrees (-90 to 90).
        longitude:      Birth location longitude in decimal degrees (-180 to 180).

    Returns:
        Solar object at the True Solar Time birth moment, ready for getLunar().
    """
    # Determine UTC offset from coordinates
    tf = TimezoneFinder()
    tz_name = tf.timezone_at(lat=latitude, lng=longitude)
    tz = ZoneInfo(tz_name)
    utc_offset_hours = birth_datetime.replace(tzinfo=tz).utcoffset().total_seconds() / 3600

    # Standard meridian: each UTC hour = 15 degrees of longitude
    standard_meridian = utc_offset_hours * 15

    # Equation of Time (minutes) — accurate to ~1 minute
    day_of_year = birth_datetime.timetuple().tm_yday
    B = (2 * math.pi / 365) * (day_of_year - 81)
    eot_minutes = 9.87 * math.sin(2 * B) - 7.53 * math.cos(B) - 1.5 * math.sin(B)

    # Longitude correction: 4 minutes per degree from standard meridian
    longitude_correction = 4 * (longitude - standard_meridian)

    # Strip tzinfo before timedelta arithmetic — handles calendar overflow/underflow
    # correctly and guards against accidentally receiving a timezone-aware datetime.
    total_adjustment_minutes = longitude_correction + eot_minutes
    naive_dt = birth_datetime.replace(tzinfo=None)
    adjusted_dt = naive_dt + timedelta(minutes=total_adjustment_minutes)

    return Solar.fromYmdHms(
        adjusted_dt.year,
        adjusted_dt.month,
        adjusted_dt.day,
        adjusted_dt.hour,
        adjusted_dt.minute,
        adjusted_dt.second,
    )
